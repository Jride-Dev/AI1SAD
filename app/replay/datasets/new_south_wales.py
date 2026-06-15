from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


_COOGEE_LAT = -33.9205
_COOGEE_LON = 151.2552


def _coogee_incident_interaction() -> dict:
    return {
        "visibility": "public",
        "observed_at": "2026-06-13T11:53:00+10:00",
        "confidence": "official",
        "fatal": False,
        "activity_context": "swimming approximately 30 m offshore",
        "source": "ABC News / NSW Ambulance source-attributed incident reporting",
        "source_url_reference": "https://www.abc.net.au/news/2026-06-13/woman-injured-after-shark-attack-sydney-coogee-beach/106794390",
        "location": {"geo": {"type": "Point", "coordinates": [_COOGEE_LON, _COOGEE_LAT]}},
        "summary": "Serious Coogee Beach swimmer incident; victim reported as a 35-year-old woman with critical but stable arm and leg injuries.",
        "distance_offshore_m": 30,
        "source_attributed_species_assessment": {
            "taxon": "suspected white shark",
            "classification_status": "preliminary_source_attributed",
            "estimated_length_m_range": "3-4",
            "model_input_for_strict_preincident": False,
        },
    }


def _coogee_closure_response_event() -> dict:
    return {
        "visibility": "public",
        "event_type": "beach_closure",
        "signal_type": "beach_closure",
        "observed_at": "2026-06-13T12:20:00+10:00",
        "confidence": 0.78,
        "value": 0.6,
        "source": "Coogee and nearby eastern-suburbs beach closure reporting",
        "location": {"geo": {"type": "Point", "coordinates": [_COOGEE_LON, _COOGEE_LAT]}},
        "location_name": "Coogee Beach, Sydney eastern suburbs, New South Wales",
        "closure_scope": "Coogee and nearby eastern-suburbs beaches",
        "notes": "Post-incident response only; excluded from strict pre-incident and quiet-day replay runs.",
    }


def _coogee_drone_restriction_context() -> dict:
    return {
        "visibility": "public",
        "event_type": "aviation_restricted_drone_review",
        "signal_type": "operational_constraint",
        "observed_at": "2026-06-14T00:00:00+10:00",
        "confidence": 0.72,
        "value": 0.0,
        "source": "ABC News / CASA source-attributed drone restriction reporting",
        "source_url_reference": "https://www.abc.net.au/news/2026-06-14/ban-lifted-coogee-drones-nsw-shark-culls-not-ruled-out/106796046",
        "location": {"geo": {"type": "Point", "coordinates": [_COOGEE_LON, _COOGEE_LAT]}},
        "location_name": "Coogee Beach, Sydney eastern suburbs, New South Wales",
        "drone_context": {
            "routine_drone_monitoring_constraint": "Sydney Airport flight-path restrictions",
            "post_incident_response": "drone and helicopter surveillance escalation",
            "emergency_use_or_exemption": "source-attributed temporary review/exemption context",
            "autonomous_flight_control": False,
            "bypass_aviation_restrictions": False,
        },
        "notes": "Operational-planning metadata only; it does not add direct warning points or imply bypassing aviation rules.",
    }


SCENARIOS = {
    "coogee_beach_sydney_2026_pre_incident": ReplayScenario(
        scenario_id="coogee_beach_sydney_2026_pre_incident",
        label="Coogee Beach Sydney 2026 strict pre-incident replay",
        lat=_COOGEE_LAT,
        lon=_COOGEE_LON,
        timestamp=datetime(2026, 6, 13, 1, 53, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        month=6,
        activity_context="swimming",
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        tags=["new_south_wales", "sydney", "coogee", "pre_incident", "timeline_strict", "swimming"],
    ),
    "coogee_beach_sydney_2026_quiet_day": ReplayScenario(
        scenario_id="coogee_beach_sydney_2026_quiet_day",
        label="Coogee Beach Sydney 2026 quiet-day swimming comparison",
        lat=_COOGEE_LAT,
        lon=_COOGEE_LON,
        timestamp=datetime(2026, 6, 13, 1, 53, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        month=6,
        activity_context="swimming",
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        tags=["new_south_wales", "sydney", "coogee", "quiet_day", "swimming"],
    ),
    "coogee_beach_sydney_2026_post_update": ReplayScenario(
        scenario_id="coogee_beach_sydney_2026_post_update",
        label="Coogee Beach Sydney 2026 post-incident operational update",
        lat=_COOGEE_LAT,
        lon=_COOGEE_LON,
        timestamp=datetime(2026, 6, 13, 2, 20, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        recent_interactions=[_coogee_incident_interaction()],
        month=6,
        activity_context="swimming",
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        tags=["new_south_wales", "sydney", "coogee", "post_incident", "closure", "swimming"],
    ),
    "coogee_beach_sydney_2026_drone_restriction_planning": ReplayScenario(
        scenario_id="coogee_beach_sydney_2026_drone_restriction_planning",
        label="Coogee Beach Sydney 2026 aviation-restricted drone planning replay",
        lat=_COOGEE_LAT,
        lon=_COOGEE_LON,
        timestamp=datetime(2026, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        recent_interactions=[_coogee_incident_interaction()],
        month=6,
        activity_context="swimming",
        suspected_species=None,
        radius_km=8.0,
        lookback_hours=96,
        expected_warning_band="low",
        tags=["new_south_wales", "sydney", "coogee", "drone_restriction", "operational_planning", "swimming"],
    ),
}
