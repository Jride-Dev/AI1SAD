from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pymongo.database import Database

from app.config import get_settings
from app.models import PaginatedIncidents, PublicIncident, PublicLocation, PublicRiskResponse, RiskSignals
from app.mongodb import COLLECTIONS, get_database, public_match
from app.risk_model import RISK_DISCLAIMER, RISK_FACTOR_DEFINITIONS, nearest_profile, score_risk
from app.services.surveillance_engine import SURVEILLANCE_DISCLAIMER, score_surveillance_zones
from app.services.signal_broker import active_public_signals, data_freshness_summary, warning_inputs_from_signals
from app.services.alert_engine import evaluate_alerts
from app.services.warning_engine import WARNING_DISCLAIMER, calculate_warning, is_stale
from providers.manual_events import build_manual_event
from providers.open_meteo import fetch_previous_72h
from app.replay.scenarios import REPLAY_SCENARIOS, ReplayScenario
from app.replay.runner import ReplayResult, ReplayRunner


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


def mongo_public_doc(document: dict[str, Any]) -> dict[str, Any]:
    result = dict(document)
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return result


def count_nearby_public_incidents(db: Database, lat: float, lon: float, radius_km: float) -> int:
    query = {
        "visibility": "public",
        "duplicate.is_duplicate": False,
        "location.geo": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius_km * 1000,
            }
        },
    }
    return sum(1 for _ in db[COLLECTIONS["incidents"]].find(query, {"_id": 1}).limit(1000))


def nearest_regional_profile(db: Database, lat: float, lon: float) -> dict[str, Any] | None:
    profiles = list(db[COLLECTIONS["regional_risk_profiles"]].find({"visibility": "public"}, {"private_notes": 0, "restricted": 0}))
    if not profiles:
        return None
    return nearest_profile(lat, lon, profiles)


def public_near_query(lat: float, lon: float, radius_km: float, geo_field: str = "location.geo") -> dict[str, Any]:
    return {
        "visibility": "public",
        geo_field: {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius_km * 1000,
            }
        },
    }


def latest_public_docs(db: Database, collection_name: str, lat: float, lon: float, radius_km: float, limit: int = 50) -> list[dict[str, Any]]:
    cursor = db[collection_name].find(public_near_query(lat, lon, radius_km), {"private_notes": 0, "restricted": 0}).limit(limit)
    return [mongo_public_doc(document) for document in cursor]


def warning_inputs_from_mongo(db: Database, lat: float, lon: float, radius_km: float) -> dict[str, Any]:
    weather_docs = latest_public_docs(db, COLLECTIONS["weather_observations"], lat, lon, radius_km)
    ocean_docs = latest_public_docs(db, COLLECTIONS["ocean_observations"], lat, lon, radius_km)
    vessel_docs = latest_public_docs(db, COLLECTIONS["vessel_activity"], lat, lon, radius_km)
    event_docs = latest_public_docs(db, COLLECTIONS["biological_events"], lat, lon, radius_km)
    exposure_docs = latest_public_docs(db, COLLECTIONS["human_exposure_estimates"], lat, lon, radius_km)
    signal_docs = latest_public_docs(db, COLLECTIONS["signals"], lat, lon, radius_km, limit=200)
    signal_inputs = warning_inputs_from_signals(signal_docs)

    rainfall = None
    if weather_docs:
        rainfall = sum(float(doc.get("rainfall_mm", doc.get("rainfall_72h_mm", 0)) or 0) for doc in weather_docs)
    if signal_inputs["rainfall_72h_mm"] is not None:
        rainfall = max(float(rainfall or 0), float(signal_inputs["rainfall_72h_mm"]))
    ocean = ocean_docs[0] if ocean_docs else {}
    vessel = vessel_docs[0] if vessel_docs else {}
    exposure = exposure_docs[0] if exposure_docs else {}
    return {
        "rainfall_72h_mm": rainfall,
        "sea_surface_temp_c": ocean.get("sea_surface_temp_c") or signal_inputs["sea_surface_temp_c"],
        "sst_anomaly_c": ocean.get("sst_anomaly_c") or signal_inputs["sst_anomaly_c"],
        "vessel_activity_index": vessel.get("activity_index") or signal_inputs["vessel_activity_index"],
        "biological_events": event_docs + signal_inputs["biological_events"],
        "human_exposure_index": exposure.get("exposure_index") or signal_inputs["human_exposure_index"],
        "signal_provider_status": signal_inputs["provider_status"],
        "signal_data_freshness": signal_inputs["data_freshness"],
        "data_presence": {
            "weather_observations": bool(weather_docs),
            "ocean_observations": bool(ocean_docs),
            "vessel_activity": bool(vessel_docs),
            "biological_events": bool(event_docs),
            "human_exposure_estimates": bool(exposure_docs),
            "signals": bool(signal_docs),
        },
    }


def cache_key_for_warning(lat: float, lon: float, radius_km: float, lookback_hours: int, month: int | None, river_mouth_distance_km: float | None) -> str:
    return "|".join(
        [
            f"{lat:.3f}",
            f"{lon:.3f}",
            f"{radius_km:.1f}",
            str(lookback_hours),
            str(month),
            str(river_mouth_distance_km),
        ]
    )


def profile_cache_ttl_minutes(db: Database, lat: float, lon: float) -> int:
    profile = nearest_regional_profile(db, lat, lon)
    if not profile:
        return 60
    return int(profile.get("warning_cache_ttl_minutes", 60))


def risk_payload(
    *,
    db: Database,
    lat: float,
    lon: float,
    radius_km: float,
    recent_rainfall_mm_24h: float,
    river_mouth_distance_km: float | None,
    sea_surface_temp_c: float | None,
    fishing_activity: float,
    baitfish_prey_indicator: float,
    water_visibility_m: float | None,
    human_water_activity: float,
    month: int | None,
    weekend: bool,
    historical_incident_count: int | None = None,
) -> PublicRiskResponse:
    incident_count = (
        historical_incident_count
        if historical_incident_count is not None
        else count_nearby_public_incidents(db, lat, lon, radius_km)
    )
    signals = {
        "historical_incident_count": incident_count,
        "recent_rainfall_mm_24h": recent_rainfall_mm_24h,
        "river_mouth_distance_km": river_mouth_distance_km,
        "sea_surface_temp_c": sea_surface_temp_c,
        "fishing_activity": fishing_activity,
        "baitfish_prey_indicator": baitfish_prey_indicator,
        "water_visibility_m": water_visibility_m,
        "human_water_activity": human_water_activity,
        "month": month,
        "weekend": weekend,
    }
    regional_profile = nearest_regional_profile(db, lat, lon)
    scored = score_risk(**signals, regional_profile=regional_profile)
    return PublicRiskResponse.model_validate(
        {
            "location": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
            "score": scored["score"],
            "band": scored["band"],
            "warning_score": scored["warning_score"],
            "warning_band": scored["warning_band"],
            "confidence": scored["confidence"],
            "signals": signals,
            "factors": scored["factors"],
            "regional_profile": scored["regional_profile"],
            "dominant_contributing_factors": scored["dominant_contributing_factors"],
            "disclaimer": scored["disclaimer"],
        }
    )


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


def serialize_alert(document: dict[str, Any]) -> dict[str, Any]:
    alert = mongo_public_doc(document)
    alert.pop("private_notes", None)
    alert.pop("restricted", None)
    return alert


@router.get("/alerts/active")
def active_alerts(
    db: Database = Depends(get_database),
    limit: Annotated[int, Query(ge=1, le=250)] = 100,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    query = {"visibility": "public", "status": "active", "expires_at": {"$gt": now}}
    projection = {"private_notes": 0, "restricted": 0}
    docs = list(db[COLLECTIONS["alerts"]].find(query, projection).limit(limit))
    return {"results": [serialize_alert(doc) for doc in docs]}


@router.get("/alerts/location")
def alerts_for_location(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 100,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    query = public_near_query(lat, lon, radius_km)
    query["status"] = "active"
    query["expires_at"] = {"$gt": now}
    docs = list(db[COLLECTIONS["alerts"]].find(query, {"private_notes": 0, "restricted": 0}).limit(limit))
    return {"results": [serialize_alert(doc) for doc in docs]}


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: str, db: Database = Depends(get_database)) -> dict[str, Any]:
    doc = db[COLLECTIONS["alerts"]].find_one({"_id": alert_id, "visibility": "public"}, {"private_notes": 0, "restricted": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Alert not found")
    return serialize_alert(doc)


@router.post("/alerts/evaluate")
def evaluate_alert_payload(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return {"alerts": evaluate_alerts(payload)}


@router.post("/admin/alerts/acknowledge")
def acknowledge_alert(payload: dict[str, Any] = Body(...), db: Database = Depends(get_database)) -> dict[str, Any]:
    if not get_settings().admin_alerts_enabled:
        raise HTTPException(status_code=403, detail="Alert admin endpoint is disabled")
    doc = {
        "alert_id": payload["alert_id"],
        "acknowledged_by": payload.get("acknowledged_by"),
        "created_at": datetime.now(timezone.utc),
        "note": payload.get("note", ""),
    }
    result = db[COLLECTIONS["alert_acknowledgements"]].insert_one(doc)
    return {"inserted_id": str(result.inserted_id), "status": "acknowledged"}


@router.post("/admin/alerts/resolve")
def resolve_alert(payload: dict[str, Any] = Body(...), db: Database = Depends(get_database)) -> dict[str, Any]:
    if not get_settings().admin_alerts_enabled:
        raise HTTPException(status_code=403, detail="Alert admin endpoint is disabled")
    result = db[COLLECTIONS["alerts"]].update_one(
        {"_id": payload["alert_id"]},
        {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc), "resolved_by": payload.get("resolved_by")}},
    )
    return {"matched_count": result.matched_count, "status": "resolved"}


@router.get("/signals/location")
def signals_for_location(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    docs = latest_public_docs(db, COLLECTIONS["signals"], lat, lon, radius_km, limit)
    return {
        "results": active_public_signals(docs),
        "data_freshness": data_freshness_summary(docs, ["open_meteo", "noaa_coastwatch", "global_fishing_watch"]),
    }


@router.get("/signals/species")
def signals_for_species(
    species: str,
    db: Database = Depends(get_database),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    projection = {"private_notes": 0, "restricted": 0}
    docs = list(
        db[COLLECTIONS["signals"]]
        .find({"visibility": "public", "species": {"$regex": species, "$options": "i"}}, projection)
        .limit(limit)
    )
    return {"results": active_public_signals([mongo_public_doc(doc) for doc in docs])}


@router.get("/signals/active")
def active_signals(
    db: Database = Depends(get_database),
    limit: Annotated[int, Query(ge=1, le=1000)] = 250,
) -> dict[str, Any]:
    projection = {"private_notes": 0, "restricted": 0}
    docs = list(db[COLLECTIONS["signals"]].find({"visibility": "public"}, projection).limit(limit))
    return {"results": active_public_signals([mongo_public_doc(doc) for doc in docs])}


@router.get("/provider-health")
def provider_health(db: Database = Depends(get_database)) -> dict[str, Any]:
    projection = {"private_notes": 0, "restricted": 0, "credentials": 0, "api_key": 0}
    health = list(db[COLLECTIONS["provider_health"]].find({}, projection).limit(500))
    recent_failures = list(db[COLLECTIONS["provider_failures"]].find({}, projection).limit(100))
    return {"providers": [mongo_public_doc(doc) for doc in health], "recent_failures": [mongo_public_doc(doc) for doc in recent_failures]}


@router.get("/regions/{region}/season-profile")
def region_season_profile(region: str, db: Database = Depends(get_database)) -> dict[str, Any]:
    projection = {"private_notes": 0, "restricted": 0}
    docs = list(
        db[COLLECTIONS["species_season_profiles"]]
        .find({"visibility": "public", "region": {"$regex": region, "$options": "i"}}, projection)
        .limit(100)
    )
    return {"region": region, "results": [mongo_public_doc(doc) for doc in docs]}


@router.get("/species/{species}/risk-profile")
def species_risk_profile(species: str, db: Database = Depends(get_database)) -> dict[str, Any]:
    projection = {"private_notes": 0, "restricted": 0}
    season_profiles = list(
        db[COLLECTIONS["species_season_profiles"]]
        .find({"visibility": "public", "species": {"$regex": species, "$options": "i"}}, projection)
        .limit(100)
    )
    migration = list(
        db[COLLECTIONS["migration_windows"]]
        .find({"visibility": "public", "species": {"$regex": species, "$options": "i"}}, projection)
        .limit(100)
    )
    signals = list(
        db[COLLECTIONS["signals"]]
        .find({"visibility": "public", "species": {"$regex": species, "$options": "i"}}, projection)
        .limit(100)
    )
    return {
        "species": species,
        "season_profiles": [mongo_public_doc(doc) for doc in season_profiles],
        "migration_windows": [mongo_public_doc(doc) for doc in migration],
        "active_signals": active_public_signals([mongo_public_doc(doc) for doc in signals]),
    }


def warning_payload(
    *,
    db: Database,
    lat: float,
    lon: float,
    radius_km: float,
    lookback_hours: int,
    month: int | None,
    river_mouth_distance_km: float | None,
    use_open_meteo: bool,
    bypass_cache: bool = False,
) -> dict[str, Any]:
    cache_key = cache_key_for_warning(lat, lon, radius_km, lookback_hours, month, river_mouth_distance_km)
    now = datetime.now(timezone.utc)
    if not bypass_cache and not use_open_meteo:
        cached = db[COLLECTIONS["warning_snapshots"]].find_one(
            {"visibility": "public", "cache_key": cache_key, "expires_at": {"$gt": now}},
            {"_id": 0, "response": 1},
        )
        if cached:
            response = dict(cached["response"])
            response["cached"] = True
            return response

    profiles = list(db[COLLECTIONS["regional_risk_profiles"]].find({"visibility": "public"}, {"private_notes": 0, "restricted": 0}))
    inputs = warning_inputs_from_mongo(db, lat, lon, radius_km)
    provider_status: dict[str, str] = {}
    if use_open_meteo and inputs["rainfall_72h_mm"] is None:
        try:
            meteo = fetch_previous_72h(lat, lon)
            inputs["rainfall_72h_mm"] = meteo.get("rainfall_72h_mm")
            provider_status["open_meteo"] = "ok"
        except Exception:
            provider_status["open_meteo"] = "unavailable"
    for source, present in inputs.pop("data_presence").items():
        provider_status[source] = "ok" if present else "missing"
    provider_status.update(inputs.pop("signal_provider_status", {}))
    signal_data_freshness = inputs.pop("signal_data_freshness", {})
    for collection_key, source in [
        ("weather_observations", "weather_observations"),
        ("ocean_observations", "ocean_observations"),
        ("vessel_activity", "vessel_activity"),
        ("human_exposure_estimates", "human_exposure_estimates"),
    ]:
        doc = db[COLLECTIONS[collection_key]].find_one(public_near_query(lat, lon, radius_km), {"observed_at": 1})
        if doc and is_stale(doc, datetime.now(timezone.utc), lookback_hours):
            provider_status[source] = "stale"
    response = calculate_warning(
        lat=lat,
        lon=lon,
        lookback_hours=lookback_hours,
        rainfall_72h_mm=inputs["rainfall_72h_mm"],
        river_mouth_distance_km=river_mouth_distance_km,
        sea_surface_temp_c=inputs["sea_surface_temp_c"],
        sst_anomaly_c=inputs["sst_anomaly_c"],
        vessel_activity_index=inputs["vessel_activity_index"],
        biological_events=inputs["biological_events"],
        human_exposure_index=inputs["human_exposure_index"],
        month=month,
        profiles=profiles,
        provider_status=provider_status,
    )
    response["data_freshness"] = {
        source: {"status": "missing"} for source, status in provider_status.items() if status == "missing"
    }
    response["data_freshness"].update(signal_data_freshness)
    ttl_minutes = profile_cache_ttl_minutes(db, lat, lon)
    snapshot = {
        "visibility": "public",
        "cache_key": cache_key,
        "created_at": now,
        "expires_at": now + timedelta(minutes=ttl_minutes),
        "ttl_minutes": ttl_minutes,
        "location": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
        "response": response,
    }
    db[COLLECTIONS["warning_snapshots"]].replace_one({"visibility": "public", "cache_key": cache_key}, snapshot, upsert=True)
    response["cached"] = False
    return response


@router.get("/warnings/location")
def warning_for_location(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 25,
    lookback_hours: Annotated[int, Query(ge=1, le=168)] = 72,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    use_open_meteo: bool = False,
    bypass_cache: bool = False,
) -> dict[str, Any]:
    return warning_payload(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
        month=month,
        river_mouth_distance_km=river_mouth_distance_km,
        use_open_meteo=use_open_meteo,
        bypass_cache=bypass_cache,
    )


@router.get("/warnings/explain")
def warning_explain(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 25,
    lookback_hours: Annotated[int, Query(ge=1, le=168)] = 72,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
) -> dict[str, Any]:
    return warning_payload(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
        month=month,
        river_mouth_distance_km=river_mouth_distance_km,
        use_open_meteo=False,
    )


@router.get("/warnings/events")
def warning_events(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
) -> dict[str, Any]:
    events = latest_public_docs(db, COLLECTIONS["biological_events"], lat, lon, radius_km, limit)
    return {"disclaimer": WARNING_DISCLAIMER, "results": events}


def surveillance_inputs_from_mongo(
    db: Database,
    lat: float,
    lon: float,
    radius_km: float,
    lookback_hours: int,
) -> dict[str, Any]:
    interactions = latest_public_docs(db, COLLECTIONS["recent_interactions"], lat, lon, radius_km)
    sightings = latest_public_docs(db, COLLECTIONS["sighting_reports"], lat, lon, radius_km)
    reefs = latest_public_docs(db, COLLECTIONS["reef_features"], lat, lon, radius_km)
    warning_inputs = warning_inputs_from_mongo(db, lat, lon, radius_km)
    provider_status = {}
    for source, present in warning_inputs.pop("data_presence").items():
        provider_status[source] = "ok" if present else "missing"
    warning_inputs["provider_status"] = provider_status
    return {
        "recent_interactions": interactions,
        "sighting_reports": sightings,
        "reef_features": reefs,
        "warning_inputs": warning_inputs,
    }


def surveillance_payload(
    *,
    db: Database,
    lat: float,
    lon: float,
    radius_km: float,
    mission_type: str,
    lookback_hours: int,
    activity_context: str | None,
    suspected_species: str | None,
    river_mouth_distance_km: float | None,
    month: int | None,
) -> dict[str, Any]:
    profiles = list(db[COLLECTIONS["regional_risk_profiles"]].find({"visibility": "public"}, {"private_notes": 0, "restricted": 0}))
    inputs = surveillance_inputs_from_mongo(db, lat, lon, radius_km, lookback_hours)
    return score_surveillance_zones(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mission_type=mission_type,
        lookback_hours=lookback_hours,
        activity_context=activity_context.lower() if activity_context else None,
        suspected_species=suspected_species,
        river_mouth_distance_km=river_mouth_distance_km,
        month=month,
        profiles=profiles,
        recent_interactions=inputs["recent_interactions"],
        sighting_reports=inputs["sighting_reports"],
        reef_features=inputs["reef_features"],
        warning_inputs=inputs["warning_inputs"],
    )


@router.get("/surveillance/search-zones")
def surveillance_search_zones(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 10,
    mission_type: str = "drone_search",
    lookback_hours: Annotated[int, Query(ge=1, le=720)] = 72,
    activity_context: str | None = None,
    suspected_species: str | None = None,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> dict[str, Any]:
    return surveillance_payload(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mission_type=mission_type,
        lookback_hours=lookback_hours,
        activity_context=activity_context,
        suspected_species=suspected_species,
        river_mouth_distance_km=river_mouth_distance_km,
        month=month,
    )


@router.get("/surveillance/explain")
def surveillance_explain(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 10,
    mission_type: str = "drone_search",
    lookback_hours: Annotated[int, Query(ge=1, le=720)] = 72,
    activity_context: str | None = None,
    suspected_species: str | None = None,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> dict[str, Any]:
    return surveillance_payload(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        mission_type=mission_type,
        lookback_hours=lookback_hours,
        activity_context=activity_context,
        suspected_species=suspected_species,
        river_mouth_distance_km=river_mouth_distance_km,
        month=month,
    )


@router.get("/surveillance/recent-interactions")
def surveillance_recent_interactions(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
) -> dict[str, Any]:
    return {
        "disclaimer": SURVEILLANCE_DISCLAIMER,
        "results": latest_public_docs(db, COLLECTIONS["recent_interactions"], lat, lon, radius_km, limit),
    }


@router.get("/surveillance/sightings")
def surveillance_sightings(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
) -> dict[str, Any]:
    return {
        "disclaimer": SURVEILLANCE_DISCLAIMER,
        "results": latest_public_docs(db, COLLECTIONS["sighting_reports"], lat, lon, radius_km, limit),
    }


def build_surveillance_event(payload: dict[str, Any], event_kind: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "visibility": str(payload.get("visibility", "private")),
        "event_kind": event_kind,
        "observed_at": payload.get("observed_at") or now,
        "created_at": now,
        "location": {"geo": {"type": "Point", "coordinates": [float(payload["lon"]), float(payload["lat"])]}},
        "species": payload.get("species"),
        "activity_context": payload.get("activity_context"),
        "fatal": bool(payload.get("fatal", False)),
        "verified": bool(payload.get("verified", False)),
        "confidence": payload.get("confidence", "unconfirmed"),
        "summary": payload.get("summary", ""),
    }


@router.post("/admin/surveillance/interaction")
def create_surveillance_interaction(payload: dict[str, Any] = Body(...), db: Database = Depends(get_database)) -> dict[str, Any]:
    if not get_settings().admin_surveillance_enabled:
        raise HTTPException(status_code=403, detail="Surveillance admin endpoint is disabled")
    event = build_surveillance_event(payload, "interaction")
    result = db[COLLECTIONS["recent_interactions"]].insert_one(event)
    return {"inserted_id": str(result.inserted_id), "status": "created"}


@router.post("/admin/surveillance/sighting")
def create_surveillance_sighting(payload: dict[str, Any] = Body(...), db: Database = Depends(get_database)) -> dict[str, Any]:
    if not get_settings().admin_surveillance_enabled:
        raise HTTPException(status_code=403, detail="Surveillance admin endpoint is disabled")
    event = build_surveillance_event(payload, "sighting")
    result = db[COLLECTIONS["sighting_reports"]].insert_one(event)
    return {"inserted_id": str(result.inserted_id), "status": "created"}


@router.post("/admin/events/manual")
def create_manual_event(payload: dict[str, Any] = Body(...), db: Database = Depends(get_database)) -> dict[str, Any]:
    if not get_settings().admin_events_enabled:
        raise HTTPException(status_code=403, detail="Manual event admin endpoint is disabled")
    event = build_manual_event(
        event_type=str(payload["event_type"]),
        lat=float(payload["lat"]),
        lon=float(payload["lon"]),
        description=str(payload.get("description", "")),
        visibility=str(payload.get("visibility", "public")),
        observed_at=payload.get("observed_at"),
        expires_at=payload.get("expires_at"),
    )
    result = db[COLLECTIONS["biological_events"]].insert_one(event)
    return {"inserted_id": str(result.inserted_id), "status": "created"}


@router.get("/risk/location", response_model=PublicRiskResponse)
def risk_for_location(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 25,
    recent_rainfall_mm_24h: Annotated[float, Query(ge=0, le=500)] = 0,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    sea_surface_temp_c: Annotated[float | None, Query(ge=-5, le=40)] = None,
    fishing_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    baitfish_prey_indicator: Annotated[float, Query(ge=0, le=1)] = 0,
    water_visibility_m: Annotated[float | None, Query(ge=0, le=100)] = None,
    human_water_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    weekend: bool = False,
) -> PublicRiskResponse:
    return risk_payload(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        recent_rainfall_mm_24h=recent_rainfall_mm_24h,
        river_mouth_distance_km=river_mouth_distance_km,
        sea_surface_temp_c=sea_surface_temp_c,
        fishing_activity=fishing_activity,
        baitfish_prey_indicator=baitfish_prey_indicator,
        water_visibility_m=water_visibility_m,
        human_water_activity=human_water_activity,
        month=month,
        weekend=weekend,
    )


@router.get("/risk/nearby")
def nearby_risk(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    recent_rainfall_mm_24h: Annotated[float, Query(ge=0, le=500)] = 0,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    sea_surface_temp_c: Annotated[float | None, Query(ge=-5, le=40)] = None,
    fishing_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    baitfish_prey_indicator: Annotated[float, Query(ge=0, le=1)] = 0,
    water_visibility_m: Annotated[float | None, Query(ge=0, le=100)] = None,
    human_water_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    weekend: bool = False,
) -> dict[str, Any]:
    location_query = {
        "visibility": "public",
        "geo": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius_km * 1000,
            }
        },
    }
    locations = list(db[COLLECTIONS["locations"]].find(location_query, {"private_notes": 0}).limit(limit))
    results = []
    for location in locations:
        coords = location.get("geo", {}).get("coordinates", [lon, lat])
        risk = risk_payload(
            db=db,
            lat=coords[1],
            lon=coords[0],
            radius_km=radius_km,
            recent_rainfall_mm_24h=recent_rainfall_mm_24h,
            river_mouth_distance_km=river_mouth_distance_km,
            sea_surface_temp_c=sea_surface_temp_c,
            fishing_activity=fishing_activity,
            baitfish_prey_indicator=baitfish_prey_indicator,
            water_visibility_m=water_visibility_m,
            human_water_activity=human_water_activity,
            month=month,
            weekend=weekend,
            historical_incident_count=location.get("incident_count", 0),
        )
        results.append({"location": mongo_public_doc(location), "risk": risk.model_dump()})
    return {"disclaimer": RISK_DISCLAIMER, "results": results}


@router.get("/risk/factors")
def risk_factors() -> dict[str, Any]:
    return {"disclaimer": RISK_DISCLAIMER, "risk_bands": ["low", "moderate", "elevated", "high"], "factors": RISK_FACTOR_DEFINITIONS}


@router.get("/risk/history")
def risk_history(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=1000)] = 50,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
) -> dict[str, Any]:
    query = {
        "visibility": "public",
        "location.geo": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius_km * 1000,
            }
        },
    }
    cursor = db[COLLECTIONS["risk_observations"]].find(query, {"private_notes": 0, "restricted": 0}).limit(limit)
    return {"disclaimer": RISK_DISCLAIMER, "results": [mongo_public_doc(document) for document in cursor]}


@router.get("/risk/explain", response_model=PublicRiskResponse)
def explain_risk(
    db: Database = Depends(get_database),
    lat: Annotated[float, Query(ge=-90, le=90)] = 0,
    lon: Annotated[float, Query(ge=-180, le=180)] = 0,
    radius_km: Annotated[float, Query(gt=0, le=250)] = 25,
    recent_rainfall_mm_24h: Annotated[float, Query(ge=0, le=500)] = 0,
    river_mouth_distance_km: Annotated[float | None, Query(ge=0, le=500)] = None,
    sea_surface_temp_c: Annotated[float | None, Query(ge=-5, le=40)] = None,
    fishing_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    baitfish_prey_indicator: Annotated[float, Query(ge=0, le=1)] = 0,
    water_visibility_m: Annotated[float | None, Query(ge=0, le=100)] = None,
    human_water_activity: Annotated[float, Query(ge=0, le=1)] = 0,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    weekend: bool = False,
) -> PublicRiskResponse:
    return risk_for_location(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        recent_rainfall_mm_24h=recent_rainfall_mm_24h,
        river_mouth_distance_km=river_mouth_distance_km,
        sea_surface_temp_c=sea_surface_temp_c,
        fishing_activity=fishing_activity,
        baitfish_prey_indicator=baitfish_prey_indicator,
        water_visibility_m=water_visibility_m,
        human_water_activity=human_water_activity,
        month=month,
        weekend=weekend,
    )


@router.get("/replay/scenarios")
def replay_list_scenarios() -> dict[str, Any]:
    summary = {}
    for sid, scenario in REPLAY_SCENARIOS.items():
        summary[sid] = {
            "label": scenario.label,
            "lat": scenario.lat,
            "lon": scenario.lon,
            "month": scenario.month,
            "activity_context": scenario.activity_context,
            "tags": scenario.tags,
        }
    return {"scenarios": summary}


@router.get("/replay/run")
def replay_run(
    scenario_id: str = "florida_summer_heavy_rain",
) -> dict[str, Any]:
    return replay_run_scenario(scenario_id)


@router.get("/replay/run/{scenario_id}")
def replay_run_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = REPLAY_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    runner = ReplayRunner()
    result = runner.run_scenario(scenario)
    if result.error:
        return {"scenario_id": scenario_id, "error": result.error}
    return _replay_response(result)


@router.post("/replay/run")
def replay_run_custom(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    scenario = ReplayScenario(
        scenario_id=payload.get("scenario_id", "custom"),
        label=payload.get("label", "Custom replay scenario"),
        lat=float(payload["lat"]),
        lon=float(payload["lon"]),
        timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")),
        rainfall_72h_mm=payload.get("rainfall_72h_mm"),
        river_mouth_distance_km=payload.get("river_mouth_distance_km"),
        sea_surface_temp_c=payload.get("sea_surface_temp_c"),
        sst_anomaly_c=payload.get("sst_anomaly_c"),
        vessel_activity_index=payload.get("vessel_activity_index"),
        human_exposure_index=payload.get("human_exposure_index"),
        biological_events=payload.get("biological_events", []),
        month=payload.get("month"),
        activity_context=payload.get("activity_context"),
        suspected_species=payload.get("suspected_species"),
        lookback_hours=payload.get("lookback_hours", 72),
        radius_km=payload.get("radius_km", 25.0),
    )
    runner = ReplayRunner()
    result = runner.run_scenario(scenario)
    if result.error:
        return {"scenario_id": scenario.scenario_id, "error": result.error}
    return _replay_response(result)


@router.get("/replay/run-all")
def replay_run_all() -> dict[str, Any]:
    runner = ReplayRunner()
    results = runner.run_all()
    return {"results": {sid: (_replay_response(res) if not res.error else {"scenario_id": sid, "error": res.error}) for sid, res in results.items()}}


@router.get("/replay/decay-analysis/{scenario_id}")
def replay_decay_analysis(scenario_id: str) -> dict[str, Any]:
    scenario = REPLAY_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    runner = ReplayRunner()
    return runner.run_decay_analysis(scenario)


@router.get("/replay/heatmap")
def replay_heatmap(
    lat: Annotated[float, Query(ge=-90, le=90)] = 27.7,
    lon: Annotated[float, Query(ge=-180, le=180)] = -80.2,
    radius_km: Annotated[float, Query(gt=0, le=200)] = 25.0,
    grid_points: Annotated[int, Query(ge=5, le=50)] = 15,
    activity_context: str | None = None,
    suspected_species: str | None = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> dict[str, Any]:
    runner = ReplayRunner()
    return runner.run_heatmap(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        grid_points=grid_points,
        activity_context=activity_context,
        suspected_species=suspected_species,
        month=month,
    )


@router.get("/replay/compare")
def replay_compare(
    scenario_id: str = "florida_summer_heavy_rain",
) -> dict[str, Any]:
    return replay_compare_quiet_day(scenario_id)


@router.get("/replay/compare-quiet-day/{scenario_id}")
def replay_compare_quiet_day(scenario_id: str) -> dict[str, Any]:
    scenario = REPLAY_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    runner = ReplayRunner()
    result = runner.run_scenario(scenario)
    if result.error:
        return {"scenario_id": scenario_id, "error": result.error}
    return {
        "scenario_id": scenario_id,
        "scenario_label": scenario.label,
        "quiet_day_comparison": result.quiet_day_comparison,
    }


def _replay_response(result: ReplayResult) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario_id,
        "label": result.label,
        "timestamp": result.timestamp.isoformat(),
        "location": result.location,
        "warning": {
            "warning_score": result.warning.get("warning_score", 0),
            "warning_band": result.warning.get("warning_band", "unknown"),
            "activity_context_score": result.warning.get("activity_context_score", 0),
            "activity_context_band": result.warning.get("activity_context_band", "unknown"),
            "confidence": result.warning.get("confidence", 0),
            "dominant_factors": result.warning.get("dominant_factors", []),
            "data_sources_used": result.warning.get("data_sources_used", []),
            "missing_data_sources": result.warning.get("missing_data_sources", []),
        },
        "surveillance": {
            "priority_score": (result.surveillance or {}).get("zones", [{}])[0].get("surveillance_priority_score", 0) if result.surveillance else 0,
            "priority_band": (result.surveillance or {}).get("zones", [{}])[0].get("surveillance_priority_band", "unknown") if result.surveillance else "unknown",
        },
        "quiet_day_comparison": result.quiet_day_comparison,
        "confidence_decomposition": result.confidence_decomposition,
    }
