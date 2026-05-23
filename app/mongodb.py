from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import ASCENDING, DESCENDING, GEOSPHERE, MongoClient
from pymongo.database import Database

from app.config import get_settings


COLLECTIONS = {
    "incidents": "incidents",
    "sources": "sources",
    "species": "species",
    "locations": "locations",
    "ingestion_runs": "ingestion_runs",
    "data_quality_reports": "data_quality_reports",
    "private_notes": "private_notes",
}


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is required")
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=10000)


def get_database() -> Database:
    return get_client()[get_settings().mongodb_database]


def public_match(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    query: dict[str, Any] = {"visibility": "public"}
    if extra:
        query.update(extra)
    return query


def ensure_mongodb_indexes(db: Database) -> None:
    incidents = db[COLLECTIONS["incidents"]]
    incidents.create_index([("visibility", ASCENDING), ("date.year", DESCENDING)])
    incidents.create_index([("visibility", ASCENDING), ("country", ASCENDING)])
    incidents.create_index([("visibility", ASCENDING), ("region", ASCENDING)])
    incidents.create_index([("visibility", ASCENDING), ("activity", ASCENDING)])
    incidents.create_index([("visibility", ASCENDING), ("species.common", ASCENDING)])
    incidents.create_index([("visibility", ASCENDING), ("fatal", ASCENDING)])
    incidents.create_index([("canonical_key", ASCENDING)])
    incidents.create_index([("source.name", ASCENDING)])
    incidents.create_index([("location.geo", GEOSPHERE)])

    db[COLLECTIONS["sources"]].create_index([("visibility", ASCENDING), ("name", ASCENDING)])
    db[COLLECTIONS["species"]].create_index([("visibility", ASCENDING), ("common", ASCENDING)])
    db[COLLECTIONS["locations"]].create_index([("visibility", ASCENDING), ("country", ASCENDING), ("region", ASCENDING)])
    db[COLLECTIONS["locations"]].create_index([("geo", GEOSPHERE)])
    db[COLLECTIONS["ingestion_runs"]].create_index([("started_at", DESCENDING)])
    db[COLLECTIONS["data_quality_reports"]].create_index([("created_at", DESCENDING)])
    db[COLLECTIONS["private_notes"]].create_index([("incident_id", ASCENDING)])

