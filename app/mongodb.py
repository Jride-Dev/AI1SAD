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
    "risk_observations": "risk_observations",
    "regional_risk_profiles": "regional_risk_profiles",
    "weather_observations": "weather_observations",
    "ocean_observations": "ocean_observations",
    "vessel_activity": "vessel_activity",
    "biological_events": "biological_events",
    "human_exposure_estimates": "human_exposure_estimates",
    "warning_snapshots": "warning_snapshots",
    "provider_runs": "provider_runs",
    "provider_failures": "provider_failures",
    "provider_health": "provider_health",
    "marine_incidents": "marine_incidents",
    "shipping_events": "shipping_events",
    "fish_kill_reports": "fish_kill_reports",
    "carcass_reports": "carcass_reports",
    "beach_closures": "beach_closures",
    "surveillance_zones": "surveillance_zones",
    "surveillance_missions": "surveillance_missions",
    "recent_interactions": "recent_interactions",
    "sighting_reports": "sighting_reports",
    "reef_features": "reef_features",
    "drone_priority_snapshots": "drone_priority_snapshots",
    "drone_missions": "drone_missions",
    "drone_telemetry": "drone_telemetry",
    "drone_observations": "drone_observations",
    "drone_attachments": "drone_attachments",
    "uav_operator_feedback": "uav_operator_feedback",
    "signals": "signals",
    "ecology_events": "ecology_events",
    "species_season_profiles": "species_season_profiles",
    "migration_windows": "migration_windows",
    "prey_presence_zones": "prey_presence_zones",
    "vessel_activity_snapshots": "vessel_activity_snapshots",
    "tourism_exposure_profiles": "tourism_exposure_profiles",
    "users": "users",
    "api_keys": "api_keys",
    "usage_logs": "usage_logs",
    "billing_tiers": "billing_tiers",
    "rate_limits": "rate_limits",
    "subscription_status": "subscription_status",
    "alerts": "alerts",
    "alert_zones": "alert_zones",
    "alert_rules": "alert_rules",
    "alert_delivery_logs": "alert_delivery_logs",
    "alert_acknowledgements": "alert_acknowledgements",
    "regional_packs": "regional_packs",
    "pack_entitlements": "pack_entitlements",
    "pack_features": "pack_features",
    "pack_replay_scenarios": "pack_replay_scenarios",
    "pack_species_profiles": "pack_species_profiles",
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
    db[COLLECTIONS["risk_observations"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["risk_observations"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["risk_observations"]].create_index([("visibility", ASCENDING), ("risk.band", ASCENDING)])
    db[COLLECTIONS["regional_risk_profiles"]].create_index([("visibility", ASCENDING), ("region_key", ASCENDING)])
    db[COLLECTIONS["regional_risk_profiles"]].create_index([("center.geo", GEOSPHERE)])
    db[COLLECTIONS["weather_observations"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["weather_observations"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["ocean_observations"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["ocean_observations"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["vessel_activity"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["vessel_activity"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["biological_events"]].create_index([("visibility", ASCENDING), ("event_type", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["biological_events"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["human_exposure_estimates"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["human_exposure_estimates"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["warning_snapshots"]].create_index([("visibility", ASCENDING), ("created_at", DESCENDING)])
    db[COLLECTIONS["warning_snapshots"]].create_index([("cache_key", ASCENDING)])
    db[COLLECTIONS["warning_snapshots"]].create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
    db[COLLECTIONS["warning_snapshots"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["provider_runs"]].create_index([("provider", ASCENDING), ("started_at", DESCENDING)])
    db[COLLECTIONS["provider_failures"]].create_index([("provider", ASCENDING), ("failed_at", DESCENDING)])
    db[COLLECTIONS["provider_health"]].create_index([("provider", ASCENDING)], unique=True)
    for event_collection in [
        "marine_incidents",
        "shipping_events",
        "fish_kill_reports",
        "carcass_reports",
        "beach_closures",
    ]:
        db[COLLECTIONS[event_collection]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
        db[COLLECTIONS[event_collection]].create_index([("location.geo", GEOSPHERE)])

    for surveillance_collection in [
        "surveillance_zones",
        "recent_interactions",
        "sighting_reports",
        "reef_features",
        "drone_priority_snapshots",
    ]:
        db[COLLECTIONS[surveillance_collection]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
        db[COLLECTIONS[surveillance_collection]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["surveillance_missions"]].create_index([("visibility", ASCENDING), ("created_at", DESCENDING)])
    db[COLLECTIONS["surveillance_missions"]].create_index([("mission_type", ASCENDING), ("status", ASCENDING)])
    db[COLLECTIONS["drone_priority_snapshots"]].create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
    db[COLLECTIONS["drone_missions"]].create_index([("visibility", ASCENDING), ("mission_id", ASCENDING)], unique=True)
    db[COLLECTIONS["drone_missions"]].create_index([("status", ASCENDING), ("started_at", DESCENDING)])
    db[COLLECTIONS["drone_telemetry"]].create_index([("visibility", ASCENDING), ("mission_id", ASCENDING), ("timestamp", DESCENDING)])
    db[COLLECTIONS["drone_telemetry"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["drone_observations"]].create_index([("visibility", ASCENDING), ("mission_id", ASCENDING), ("timestamp", DESCENDING)])
    db[COLLECTIONS["drone_observations"]].create_index([("visibility", ASCENDING), ("observation_type", ASCENDING), ("review_status", ASCENDING)])
    db[COLLECTIONS["drone_observations"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["drone_attachments"]].create_index([("observation_id", ASCENDING), ("uploaded_at", DESCENDING)])
    db[COLLECTIONS["drone_attachments"]].create_index([("mission_id", ASCENDING), ("review_visibility", ASCENDING)])
    db[COLLECTIONS["uav_operator_feedback"]].create_index([("submitted_at", DESCENDING)])
    db[COLLECTIONS["uav_operator_feedback"]].create_index([("review_status", ASCENDING), ("submitted_at", DESCENDING)])

    db[COLLECTIONS["signals"]].create_index([("visibility", ASCENDING), ("signal_type", ASCENDING), ("timestamp", DESCENDING)])
    db[COLLECTIONS["signals"]].create_index([("visibility", ASCENDING), ("species", ASCENDING), ("timestamp", DESCENDING)])
    db[COLLECTIONS["signals"]].create_index([("visibility", ASCENDING), ("expires_at", ASCENDING)])
    db[COLLECTIONS["signals"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["ecology_events"]].create_index([("visibility", ASCENDING), ("event_type", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["ecology_events"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["species_season_profiles"]].create_index([("visibility", ASCENDING), ("region", ASCENDING), ("species", ASCENDING)])
    db[COLLECTIONS["migration_windows"]].create_index([("visibility", ASCENDING), ("region", ASCENDING), ("species", ASCENDING)])
    db[COLLECTIONS["prey_presence_zones"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["prey_presence_zones"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["vessel_activity_snapshots"]].create_index([("visibility", ASCENDING), ("observed_at", DESCENDING)])
    db[COLLECTIONS["vessel_activity_snapshots"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["tourism_exposure_profiles"]].create_index([("visibility", ASCENDING), ("region", ASCENDING)])

    db[COLLECTIONS["users"]].create_index([("email", ASCENDING)], unique=True, sparse=True)
    db[COLLECTIONS["users"]].create_index([("created_at", DESCENDING)])
    db[COLLECTIONS["api_keys"]].create_index([("key_hash", ASCENDING)], unique=True)
    db[COLLECTIONS["api_keys"]].create_index([("user_id", ASCENDING), ("status", ASCENDING)])
    db[COLLECTIONS["usage_logs"]].create_index([("api_key_id", ASCENDING), ("timestamp", DESCENDING)])
    db[COLLECTIONS["usage_logs"]].create_index([("timestamp", DESCENDING)])
    db[COLLECTIONS["billing_tiers"]].create_index([("tier", ASCENDING)], unique=True)
    db[COLLECTIONS["rate_limits"]].create_index([("tier", ASCENDING), ("route_group", ASCENDING)], unique=True)
    db[COLLECTIONS["subscription_status"]].create_index([("user_id", ASCENDING)], unique=True)
    db[COLLECTIONS["subscription_status"]].create_index([("tier", ASCENDING), ("status", ASCENDING)])

    db[COLLECTIONS["alerts"]].create_index([("visibility", ASCENDING), ("status", ASCENDING), ("expires_at", ASCENDING)])
    db[COLLECTIONS["alerts"]].create_index([("alert_type", ASCENDING), ("level", ASCENDING)])
    db[COLLECTIONS["alerts"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["alert_zones"]].create_index([("visibility", ASCENDING), ("created_at", DESCENDING)])
    db[COLLECTIONS["alert_zones"]].create_index([("location.geo", GEOSPHERE)])
    db[COLLECTIONS["alert_rules"]].create_index([("alert_type", ASCENDING), ("status", ASCENDING)])
    db[COLLECTIONS["alert_delivery_logs"]].create_index([("alert_id", ASCENDING), ("created_at", DESCENDING)])
    db[COLLECTIONS["alert_acknowledgements"]].create_index([("alert_id", ASCENDING), ("created_at", DESCENDING)])

    db[COLLECTIONS["regional_packs"]].create_index([("visibility", ASCENDING), ("pack_id", ASCENDING)], unique=True)
    db[COLLECTIONS["regional_packs"]].create_index([("center.geo", GEOSPHERE)])
    db[COLLECTIONS["pack_entitlements"]].create_index([("visibility", ASCENDING), ("pack_id", ASCENDING), ("status", ASCENDING)])
    db[COLLECTIONS["pack_features"]].create_index([("visibility", ASCENDING), ("pack_id", ASCENDING), ("feature_key", ASCENDING)])
    db[COLLECTIONS["pack_replay_scenarios"]].create_index([("visibility", ASCENDING), ("pack_id", ASCENDING), ("scenario_id", ASCENDING)])
    db[COLLECTIONS["pack_species_profiles"]].create_index([("visibility", ASCENDING), ("pack_id", ASCENDING), ("species", ASCENDING)])
