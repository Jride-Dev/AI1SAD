from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.models import PaginatedIncidents, PublicIncident
from app.mongodb import COLLECTIONS, get_database, public_match


router = APIRouter(prefix="/api/v1")


def public_incident_filter(
    year: int | None = None,
    country: str | None = None,
    region: str | None = None,
    activity: str | None = None,
    fatal: bool | None = None,
    species: str | None = None,
    include_duplicates: bool = False,
) -> dict[str, Any]:
    query: dict[str, Any] = {"visibility": "public"}
    if not include_duplicates:
        query["duplicate.is_duplicate"] = False
    if year is not None:
        query["date.year"] = year
    if country:
        query["country"] = country.upper()
    if region:
        query["region"] = region
    if activity:
        query["activity"] = activity.lower()
    if fatal is not None:
        query["fatal"] = fatal
    if species:
        query["species.common"] = {"$regex": species, "$options": "i"}
    return query


def serialize_incident(document: dict[str, Any]) -> PublicIncident:
    document = dict(document)
    document["_id"] = str(document["_id"])
    return PublicIncident.model_validate(document)


@router.get("/incidents", response_model=PaginatedIncidents, response_model_by_alias=False)
def list_incidents(
    db: Database = Depends(get_database),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    year: int | None = None,
    country: str | None = None,
    region: str | None = None,
    activity: str | None = None,
    fatal: bool | None = None,
    species: str | None = None,
    include_duplicates: bool = False,
) -> dict[str, Any]:
    query = public_incident_filter(year, country, region, activity, fatal, species, include_duplicates)
    collection = db[COLLECTIONS["incidents"]]
    cursor = collection.find(query).sort([("date.year", -1), ("_id", 1)]).skip(offset).limit(limit)
    return {
        "count": collection.count_documents(query),
        "limit": limit,
        "offset": offset,
        "results": [serialize_incident(document) for document in cursor],
    }


@router.get("/incidents/{incident_id}", response_model=PublicIncident, response_model_by_alias=False)
def get_incident(incident_id: str, db: Database = Depends(get_database)) -> PublicIncident:
    document = db[COLLECTIONS["incidents"]].find_one({"_id": incident_id, "visibility": "public"})
    if not document:
        raise HTTPException(status_code=404, detail="Incident not found")
    return serialize_incident(document)


def grouped_stats(db: Database, field: str, limit: int = 250, sort_by_key_desc: bool = False) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"visibility": "public", "duplicate.is_duplicate": False, field: {"$ne": None}}},
        {
            "$group": {
                "_id": f"${field}",
                "incidents": {"$sum": 1},
                "fatalities": {"$sum": {"$cond": ["$fatal", 1, 0]}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "key": "$_id",
                "incidents": 1,
                "fatalities": 1,
                "fatality_rate_percent": {
                    "$round": [{"$multiply": [{"$divide": ["$fatalities", "$incidents"]}, 100]}, 2]
                },
            }
        },
        {"$sort": {"key": -1} if sort_by_key_desc else {"incidents": -1, "key": 1}},
        {"$limit": limit},
    ]
    return list(db[COLLECTIONS["incidents"]].aggregate(pipeline))


@router.get("/stats/yearly")
def yearly_stats(db: Database = Depends(get_database)) -> list[dict[str, Any]]:
    return grouped_stats(db, "date.year", limit=1000, sort_by_key_desc=True)


@router.get("/stats/by-country")
def stats_by_country(db: Database = Depends(get_database), limit: Annotated[int, Query(ge=1, le=500)] = 250) -> list[dict[str, Any]]:
    return grouped_stats(db, "country", limit)


@router.get("/stats/by-region")
def stats_by_region(db: Database = Depends(get_database), limit: Annotated[int, Query(ge=1, le=500)] = 250) -> list[dict[str, Any]]:
    return grouped_stats(db, "region", limit)


@router.get("/stats/by-activity")
def stats_by_activity(db: Database = Depends(get_database), limit: Annotated[int, Query(ge=1, le=500)] = 250) -> list[dict[str, Any]]:
    return grouped_stats(db, "activity", limit)


@router.get("/stats/by-species")
def stats_by_species(db: Database = Depends(get_database), limit: Annotated[int, Query(ge=1, le=500)] = 250) -> list[dict[str, Any]]:
    return grouped_stats(db, "species.common", limit)


@router.get("/stats/fatality-rate")
def fatality_rate(db: Database = Depends(get_database)) -> dict[str, Any]:
    pipeline = [
        {"$match": {"visibility": "public", "duplicate.is_duplicate": False}},
        {"$group": {"_id": None, "incidents": {"$sum": 1}, "fatalities": {"$sum": {"$cond": ["$fatal", 1, 0]}}}},
        {
            "$project": {
                "_id": 0,
                "incidents": 1,
                "fatalities": 1,
                "fatality_rate_percent": {
                    "$cond": [
                        {"$eq": ["$incidents", 0]},
                        None,
                        {"$round": [{"$multiply": [{"$divide": ["$fatalities", "$incidents"]}, 100]}, 2]},
                    ]
                },
            }
        },
    ]
    rows = list(db[COLLECTIONS["incidents"]].aggregate(pipeline))
    return rows[0] if rows else {"incidents": 0, "fatalities": 0, "fatality_rate_percent": None}


@router.get("/locations/nearby")
def nearby_locations(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
) -> list[dict[str, Any]]:
    query = {
        "visibility": "public",
        "geo": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius_km * 1000,
            }
        },
    }
    projection = {"private_notes": 0, "restricted": 0}
    return list(db[COLLECTIONS["locations"]].find(query, projection).limit(limit))


@router.get("/sources")
def sources(db: Database = Depends(get_database), limit: Annotated[int, Query(ge=1, le=250)] = 100) -> list[dict[str, Any]]:
    projection = {"private_notes": 0, "restricted": 0}
    return list(db[COLLECTIONS["sources"]].find(public_match(), projection).sort("name", 1).limit(limit))
