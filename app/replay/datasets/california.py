from __future__ import annotations

from datetime import datetime, timezone

from app.providers.kelp_forest import normalize_static_kelp_forest_signals
from app.replay.scenarios import ReplayScenario


_LOVERS_POINT_LAT = 36.625
_LOVERS_POINT_LON = -121.916


def _lovers_point_kelp_signals() -> list[dict]:
    return normalize_static_kelp_forest_signals(
        lat=_LOVERS_POINT_LAT,
        lon=_LOVERS_POINT_LON,
        radius_km=8.0,
        lookback_hours=720,
    )


def _lovers_point_carcass_event() -> dict:
    return {
        "visibility": "public",
        "event_type": "whale_carcass",
        "signal_type": "whale_carcass",
        "observed_at": "2026-06-03T12:55:00-07:00",
        "confidence": 0.86,
        "value": 1.0,
        "source": "City of Pacific Grove / Pacific Grove Police source-attributed closure notice",
        "location": {"geo": {"type": "Point", "coordinates": [_LOVERS_POINT_LON, _LOVERS_POINT_LAT]}},
        "location_name": "Lovers Point, Pacific Grove, Monterey County, California",
        "whale_taxon": "humpback whale",
        "official_species_identification": "humpback whale",
        "taxonomy_status": "official_city_follow_up",
        "taxonomy_confidence": "official_follow_up",
        "historical_conflicting_identification": "Earlier conflicting species references, if present, are retained only as source-attributed historical metadata.",
        "beach_closure": True,
        "closure_scope": "temporary Lovers Point beach-access closure",
        "closure_monitoring_through": "2026-06-05",
        "authority_concern": "Marine mammal carcasses can attract sharks, particularly larger predatory species.",
        "drift_direction": "unavailable",
        "drift_speed": "unavailable",
        "tide_current_support": "not_available_for_this_fixture",
        "notes": "No shark sighting or drift path is asserted in the verified carcass-response scenario.",
    }


def _lovers_point_closure_event() -> dict:
    return {
        "visibility": "public",
        "event_type": "beach_closure",
        "signal_type": "beach_closure",
        "observed_at": "2026-06-03T12:55:00-07:00",
        "confidence": 0.8,
        "value": 0.6,
        "source": "Pacific Grove authority closure metadata",
        "location": {"geo": {"type": "Point", "coordinates": [_LOVERS_POINT_LON, _LOVERS_POINT_LAT]}},
        "location_name": "Lovers Point, Pacific Grove, Monterey County, California",
        "closure_monitoring_through": "2026-06-05",
    }


def _hypothetical_lovers_point_sighting() -> dict:
    return {
        "visibility": "public",
        "source": "hypothetical_sensitivity_input",
        "confidence": "official",
        "verified": True,
        "hypothetical": True,
        "observed_at": "2026-06-03T14:00:00-07:00",
        "location": {"geo": {"type": "Point", "coordinates": [_LOVERS_POINT_LON, _LOVERS_POINT_LAT]}},
        "summary": "Hypothetical only: nearby shark sighting used to test surveillance-priority sensitivity near a whale carcass.",
    }


SCENARIOS = {
    "lovers_point_pacific_grove_whale_carcass_2026_initial": ReplayScenario(
        scenario_id="lovers_point_pacific_grove_whale_carcass_2026_initial",
        label="Lovers Point Pacific Grove whale carcass response replay",
        lat=_LOVERS_POINT_LAT,
        lon=_LOVERS_POINT_LON,
        timestamp=datetime(2026, 6, 3, 19, 55, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        biological_events=[_lovers_point_carcass_event(), _lovers_point_closure_event()],
        kelp_habitat_signals=_lovers_point_kelp_signals(),
        month=6,
        activity_context=None,
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=168,
        expected_warning_band="low",
        tags=["california", "monterey", "lovers_point", "whale_carcass", "closure", "timeline_strict"],
    ),
    "lovers_point_pacific_grove_whale_carcass_2026_drift_planning": ReplayScenario(
        scenario_id="lovers_point_pacific_grove_whale_carcass_2026_drift_planning",
        label="Lovers Point Pacific Grove whale carcass drift-corridor planning replay",
        lat=_LOVERS_POINT_LAT,
        lon=_LOVERS_POINT_LON,
        timestamp=datetime(2026, 6, 5, 19, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        biological_events=[_lovers_point_carcass_event(), _lovers_point_closure_event()],
        kelp_habitat_signals=_lovers_point_kelp_signals(),
        month=6,
        activity_context=None,
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=168,
        expected_warning_band="low",
        tags=["california", "monterey", "lovers_point", "whale_carcass", "drift_planning", "no_drift_fixture"],
    ),
    "lovers_point_pacific_grove_whale_carcass_2026_hypothetical_sighting": ReplayScenario(
        scenario_id="lovers_point_pacific_grove_whale_carcass_2026_hypothetical_sighting",
        label="Lovers Point Pacific Grove whale carcass hypothetical nearby-sighting sensitivity replay",
        lat=_LOVERS_POINT_LAT,
        lon=_LOVERS_POINT_LON,
        timestamp=datetime(2026, 6, 3, 21, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        biological_events=[_lovers_point_carcass_event(), _lovers_point_closure_event()],
        sighting_reports=[_hypothetical_lovers_point_sighting()],
        kelp_habitat_signals=_lovers_point_kelp_signals(),
        month=6,
        activity_context=None,
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=168,
        expected_warning_band="low",
        tags=["california", "monterey", "lovers_point", "whale_carcass", "hypothetical", "sighting_sensitivity"],
    ),
}
