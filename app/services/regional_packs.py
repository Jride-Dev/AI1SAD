from __future__ import annotations

from copy import deepcopy
from typing import Any

from pymongo.database import Database

from app.mongodb import COLLECTIONS
from app.risk_model import haversine_km


PACK_NOTICE = (
    "A higher-resolution regional pack is available for this location. Core remains available; "
    "regional packs are soft-gated and not hard billing enforcement."
)


INITIAL_REGIONAL_PACKS: list[dict[str, Any]] = [
    {
        "_id": "core",
        "pack_id": "core",
        "visibility": "public",
        "name": "AI1SAD Core",
        "covered_regions": ["global"],
        "center": {"geo": {"type": "Point", "coordinates": [0, 0]}},
        "coverage_radius_km": 20040,
        "dominant_species": ["white shark", "tiger shark", "bull shark", "blacktip shark"],
        "seasonal_windows": {"global": "No single global summer definition; use regional packs for local seasonality."},
        "environmental_signals": ["rainfall", "runoff", "SST", "vessel_activity", "biological_events", "kelp_forest_context"],
        "human_exposure_signals": ["activity_context", "beach_exposure", "tourism_exposure"],
        "surveillance_rules": ["recent_interactions", "sightings", "habitat_features", "activity_hazard"],
        "alert_rules": ["general_warning", "surveillance_priority", "activity_hazard", "biological_event"],
        "replay_scenarios": ["florida_summer_heavy_rain", "wa_spearfishing_reef_white"],
        "docs_links": ["docs/REGIONAL_PACKS.md", "docs/PACK_ENTITLEMENTS.md"],
        "required_access_tier": "free",
        "features": ["core_warning", "core_surveillance", "core_replay", "core_alerts"],
    },
    {
        "_id": "florida",
        "pack_id": "florida",
        "visibility": "public",
        "name": "Florida Regional Pack",
        "covered_regions": ["Florida", "U.S. Southeast Atlantic", "Gulf coast"],
        "center": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
        "coverage_radius_km": 900,
        "dominant_species": ["bull shark", "blacktip shark", "spinner shark"],
        "seasonal_windows": {"high_exposure_months": [5, 6, 7, 8, 9], "tourist_attention_months": [3, 4, 10]},
        "environmental_signals": ["rainfall_runoff", "inlet_proximity", "baitfish", "SST"],
        "human_exposure_signals": ["weekend", "beach_exposure", "surfing", "fishing"],
        "surveillance_rules": ["inlet_runoff", "surf_fishing_context", "blacktip_bull_context"],
        "alert_rules": ["crowded_beach_inlet_rainfall", "activity_hazard"],
        "replay_scenarios": ["florida_summer_heavy_rain"],
        "docs_links": ["docs/REGIONAL_RISK_PROFILES.md", "docs/REPLAY_ENGINE.md"],
        "required_access_tier": "developer",
        "features": ["florida_species_context", "florida_inlet_rules", "florida_replays"],
    },
    {
        "_id": "hawaii",
        "pack_id": "hawaii",
        "visibility": "public",
        "name": "Hawaii Regional Pack",
        "covered_regions": ["Hawaii"],
        "center": {"geo": {"type": "Point", "coordinates": [-157.8, 21.3]}},
        "coverage_radius_km": 650,
        "dominant_species": ["tiger shark", "reef shark", "galapagos shark"],
        "seasonal_windows": {"high_attention_months": [10], "sharktober": [10]},
        "environmental_signals": ["turtle_prey_context", "SST", "biological_events", "reef_channel_habitat", "shallow_reef_habitat", "reef_edge_habitat", "hardbottom_habitat", "sandy_bottom_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "human_exposure_signals": ["surfing", "swimming", "diving", "tourism_exposure"],
        "surveillance_rules": ["hawaii_october_tiger_context", "sighting_cluster", "reef_channel_context", "reef_edge_context", "habitat_visibility_context"],
        "alert_rules": ["hawaii_october_tiger_watch"],
        "replay_scenarios": ["hawaii_october_tiger_context"],
        "docs_links": ["docs/REGIONAL_RISK_PROFILES.md"],
        "required_access_tier": "developer",
        "features": ["hawaii_sharktober", "tiger_shark_context", "hawaii_replays", "hawaii_habitat_baseline_context"],
    },
    {
        "_id": "western_australia",
        "pack_id": "western_australia",
        "visibility": "public",
        "name": "Western Australia Regional Pack",
        "covered_regions": ["Western Australia"],
        "center": {"geo": {"type": "Point", "coordinates": [115.8, -31.9]}},
        "coverage_radius_km": 1800,
        "dominant_species": ["white shark", "tiger shark", "bronze whaler"],
        "seasonal_windows": {"australia_high_exposure_months": [1, 2]},
        "environmental_signals": ["reef_habitat", "dropoff_habitat", "kelp_forest_context", "SST", "biological_events"],
        "human_exposure_signals": ["spearfishing", "diving_with_catch", "surfing", "fishing"],
        "surveillance_rules": ["white_shark_reef_spearfishing", "white_shark_kelp_edge_context", "post_incident_surveillance"],
        "alert_rules": ["urgent_surveillance_low_warning_split"],
        "replay_scenarios": ["wa_spearfishing_reef_white", "horseshoe_reef_2026_replay"],
        "docs_links": ["docs/CASE_STUDY_HORSESHOE_REEF_2026.md", "docs/SURVEILLANCE_ENGINE.md"],
        "required_access_tier": "research",
        "features": ["wa_white_shark_context", "wa_reef_surveillance", "wa_replays"],
    },
    {
        "_id": "new_south_wales",
        "pack_id": "new_south_wales",
        "visibility": "public",
        "name": "New South Wales Regional Pack",
        "covered_regions": ["New South Wales", "NSW"],
        "center": {"geo": {"type": "Point", "coordinates": [151.2, -33.9]}},
        "coverage_radius_km": 900,
        "dominant_species": ["bull shark", "white shark", "whaler shark"],
        "seasonal_windows": {"australia_high_exposure_months": [1, 2]},
        "environmental_signals": ["river_mouth_runoff", "SST", "rainfall"],
        "human_exposure_signals": ["surfing", "swimming", "fishing"],
        "surveillance_rules": ["bull_shark_river_mouth_runoff", "surf_zone_attention"],
        "alert_rules": ["runoff_watch", "surveillance_priority"],
        "replay_scenarios": ["nsw_bull_shark_runoff"],
        "docs_links": ["docs/REGIONAL_RISK_PROFILES.md"],
        "required_access_tier": "research",
        "features": ["nsw_bull_shark_runoff", "southern_hemisphere_seasonality"],
    },
    {
        "_id": "south_africa",
        "pack_id": "south_africa",
        "visibility": "public",
        "name": "South Africa Regional Pack",
        "covered_regions": ["South Africa"],
        "center": {"geo": {"type": "Point", "coordinates": [18.4, -34.1]}},
        "coverage_radius_km": 1200,
        "dominant_species": ["white shark", "bronze whaler"],
        "seasonal_windows": {"seal_colony_attention": [5, 6, 7, 8, 9]},
        "environmental_signals": ["seal_colony_context", "kelp_forest_context", "SST", "visibility"],
        "human_exposure_signals": ["surfing", "diving", "swimming"],
        "surveillance_rules": ["seal_colony_surf_context", "white_shark_habitat", "kelp_edge_prey_overlap"],
        "alert_rules": ["surf_seal_colony_watch"],
        "replay_scenarios": ["south_africa_white_shark_surf_seal_colony"],
        "docs_links": ["docs/REPLAY_ENGINE.md"],
        "required_access_tier": "research",
        "features": ["south_africa_white_shark_context", "seal_colony_replays"],
    },
    {
        "_id": "red_sea",
        "pack_id": "red_sea",
        "visibility": "public",
        "name": "Red Sea Regional Pack",
        "covered_regions": ["Red Sea", "Egypt", "Saudi Arabia"],
        "center": {"geo": {"type": "Point", "coordinates": [38.5, 20.5]}},
        "coverage_radius_km": 1600,
        "dominant_species": ["oceanic whitetip shark", "tiger shark", "grey reef shark"],
        "seasonal_windows": {"tourism_attention": [5, 6, 7, 8, 9, 10]},
        "environmental_signals": ["carcass_reports", "shipping_events", "feeding_event_sensitivity"],
        "human_exposure_signals": ["tourism_exposure", "diving", "snorkeling"],
        "surveillance_rules": ["carcass_shipping_anomaly", "tourism_exposure"],
        "alert_rules": ["biological_event_advisory", "shipping_anomaly_advisory"],
        "replay_scenarios": ["red_sea_carcass_shipping_anomaly"],
        "docs_links": ["docs/CURRENT_DATA_SOURCES.md", "docs/ALERT_ENGINE.md"],
        "required_access_tier": "government_enterprise",
        "features": ["red_sea_event_intelligence", "shipping_anomaly_context"],
    },
    {
        "_id": "us_east_coast",
        "pack_id": "us_east_coast",
        "visibility": "public",
        "name": "U.S. East Coast Regional Pack",
        "covered_regions": ["U.S. East Coast", "Carolinas", "Northeast U.S."],
        "center": {"geo": {"type": "Point", "coordinates": [-74.0, 36.5]}},
        "coverage_radius_km": 1700,
        "dominant_species": ["sand tiger shark", "blacktip shark", "spinner shark", "white shark"],
        "seasonal_windows": {"summer_exposure": [6, 7, 8, 9]},
        "environmental_signals": ["nearshore_baitfish", "SST", "tourism_exposure"],
        "human_exposure_signals": ["swimming", "surfing", "fishing"],
        "surveillance_rules": ["beach_exposure", "baitfish_nearshore"],
        "alert_rules": ["summer_beach_watch", "sighting_cluster"],
        "replay_scenarios": [],
        "docs_links": ["docs/REGIONAL_PACKS.md"],
        "required_access_tier": "developer",
        "features": ["us_east_coast_seasonality", "nearshore_baitfish_context"],
    },
]


def initial_pack_map() -> dict[str, dict[str, Any]]:
    return {pack["pack_id"]: deepcopy(pack) for pack in INITIAL_REGIONAL_PACKS}


def sanitize_pack(pack: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(pack)
    result.pop("private_notes", None)
    result.pop("restricted", None)
    result.pop("internal_rules", None)
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return result


def load_public_packs(db: Database | None = None) -> list[dict[str, Any]]:
    if db is None:
        return [sanitize_pack(pack) for pack in INITIAL_REGIONAL_PACKS]
    try:
        docs = list(db[COLLECTIONS["regional_packs"]].find({"visibility": "public"}, {"private_notes": 0, "restricted": 0, "internal_rules": 0}))
    except Exception:
        docs = []
    if not docs:
        docs = INITIAL_REGIONAL_PACKS
    return [sanitize_pack(pack) for pack in docs if pack.get("visibility", "public") == "public"]


def nearest_available_pack(lat: float, lon: float, packs: list[dict[str, Any]]) -> dict[str, Any] | None:
    regional = [pack for pack in packs if pack.get("pack_id") != "core"]
    candidates = []
    for pack in regional:
        coords = pack.get("center", {}).get("geo", {}).get("coordinates")
        if not coords or len(coords) < 2:
            continue
        distance = haversine_km(lon, lat, coords[0], coords[1])
        if distance <= float(pack.get("coverage_radius_km", 0) or 0):
            candidates.append((distance, pack))
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])[1]


def enabled_pack_ids(db: Database | None = None, requested: list[str] | None = None) -> set[str]:
    enabled = {"core"}
    if requested:
        enabled.update(pack.strip() for pack in requested if pack.strip())
    if db is not None:
        try:
            docs = list(db[COLLECTIONS["pack_entitlements"]].find({"visibility": "public", "status": "active"}, {"private_notes": 0, "restricted": 0}))
        except Exception:
            docs = []
        for doc in docs:
            pack_id = doc.get("pack_id")
            if pack_id:
                enabled.add(str(pack_id))
    return enabled


def pack_context(
    db: Database | None,
    *,
    lat: float | None = None,
    lon: float | None = None,
    enabled_packs: list[str] | None = None,
) -> dict[str, Any]:
    packs = load_public_packs(db)
    pack_map = {pack["pack_id"]: pack for pack in packs}
    enabled = enabled_pack_ids(db, enabled_packs)
    available = nearest_available_pack(lat, lon, packs) if lat is not None and lon is not None else None
    active = "core"
    notice = None
    if available:
        available_id = available["pack_id"]
        if available_id in enabled:
            active = available_id
        else:
            notice = PACK_NOTICE
    active_pack = pack_map.get(active, pack_map.get("core", initial_pack_map()["core"]))
    features = active_pack.get("features", [])
    return {
        "active_pack": active_pack["pack_id"],
        "active_pack_name": active_pack.get("name"),
        "pack_features_used": features,
        "pack_notice": notice,
        "available_pack": available["pack_id"] if available else None,
        "available_pack_name": available.get("name") if available else None,
        "enabled_packs": sorted(enabled),
    }


def annotate_response_with_pack(
    response: dict[str, Any],
    db: Database | None,
    *,
    lat: float | None,
    lon: float | None,
    enabled_packs: list[str] | None = None,
) -> dict[str, Any]:
    context = pack_context(db, lat=lat, lon=lon, enabled_packs=enabled_packs)
    response.update(
        {
            "active_pack": context["active_pack"],
            "pack_features_used": context["pack_features_used"],
            "pack_notice": context["pack_notice"],
        }
    )
    if context["available_pack"]:
        response["available_pack"] = context["available_pack"]
    return response


def pack_entitlement_summary(db: Database | None = None, requested: list[str] | None = None) -> dict[str, Any]:
    packs = load_public_packs(db)
    enabled = enabled_pack_ids(db, requested)
    return {
        "soft_entitlements_only": True,
        "enabled_packs": sorted(enabled),
        "available_packs": [
            {
                "pack_id": pack["pack_id"],
                "name": pack.get("name"),
                "required_access_tier": pack.get("required_access_tier"),
                "enabled": pack["pack_id"] in enabled,
            }
            for pack in packs
        ],
    }
