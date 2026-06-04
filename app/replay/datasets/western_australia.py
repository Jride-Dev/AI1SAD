from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


_PLUMPUDDING_LAT = -33.90
_PLUMPUDDING_LON = 121.65


def _plumpudding_carcass_event() -> dict:
    return {
        "visibility": "public",
        "event_type": "whale carcass",
        "signal_type": "whale_carcass",
        "observed_at": "2026-05-29T14:00:00+08:00",
        "confidence": 0.82,
        "value": 1.0,
        "source": "WA SharkSmart Shark ADVICE for Plumpudding Beach, west of Esperance",
        "source_url_reference": "https://www.sharksmart.com.au/shark-activity/",
        "location": {"geo": {"type": "Point", "coordinates": [_PLUMPUDDING_LON, _PLUMPUDDING_LAT]}},
        "location_name": "Plumpudding Beach near Butty Head, Shire of Esperance, Western Australia",
        "reported_times": {
            "earliest_source_attributed_sighting": "2026-05-29T14:00:00+08:00",
            "sharksmart_member_of_public_report": "approximately 2026-05-29T14:30:00+08:00",
            "slswa_sighted_at": "2026-05-29T14:00:00+08:00",
            "slswa_logged_at": "2026-05-29T15:04:00+08:00",
        },
        "whale_taxon": "Kogia sp.",
        "possible_species": "Kogia breviceps",
        "taxonomy_status": "provisional",
        "taxonomy_confidence": "provisional_unverified",
        "estimated_length_m": None,
        "carcass_mass_class": "small_whale",
        "decomposition_state": "not_reported",
        "distance_to_shore_m": 1,
        "drift_direction": "not_reported",
        "drift_speed": "not_reported",
        "residue_present": "unknown",
        "removal_status": "not_reported",
        "last_verified_at": "2026-05-29T15:04:00+08:00",
        "official_species_identification": None,
        "notes": "Official alert did not identify whale species; Kogia fields are provisional context only.",
    }


def _hypothetical_nearby_sighting() -> dict:
    return {
        "visibility": "public",
        "source": "hypothetical_sensitivity_input",
        "confidence": "official",
        "verified": True,
        "hypothetical": True,
        "observed_at": "2026-05-29T15:10:00+08:00",
        "location": {"geo": {"type": "Point", "coordinates": [_PLUMPUDDING_LON, _PLUMPUDDING_LAT]}},
        "summary": "Hypothetical only: nearby shark sighting used to test surveillance-priority sensitivity.",
    }


SCENARIOS = {
    "wa_spearfishing_reef_white": ReplayScenario(
        scenario_id="wa_spearfishing_reef_white",
        label="Western Australia spearfishing on reef with white shark suitability",
        lat=-31.95,
        lon=115.86,
        timestamp=datetime(2025, 2, 10, 8, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=0.0,
        river_mouth_distance_km=15.0,
        sea_surface_temp_c=22.0,
        sst_anomaly_c=0.0,
        vessel_activity_index=0.2,
        human_exposure_index=0.3,
        month=2,
        activity_context="spearfishing",
        suspected_species="white shark",
        radius_km=10.0,
        expected_surveillance_band="elevated",
        tags=["western_australia", "spearfishing", "reef", "white_shark"],
    ),
    "plumpudding_beach_esperance_whale_carcass_2026_initial": ReplayScenario(
        scenario_id="plumpudding_beach_esperance_whale_carcass_2026_initial",
        label="Plumpudding Beach Esperance whale carcass operational replay (initial report)",
        lat=_PLUMPUDDING_LAT,
        lon=_PLUMPUDDING_LON,
        timestamp=datetime(2026, 5, 29, 6, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        biological_events=[_plumpudding_carcass_event()],
        month=5,
        activity_context=None,
        suspected_species=None,
        radius_km=10.0,
        lookback_hours=168,
        expected_warning_band="low",
        tags=["western_australia", "esperance", "whale_carcass", "initial_report", "timeline_strict"],
    ),
    "plumpudding_beach_esperance_whale_carcass_2026_hypothetical_sighting": ReplayScenario(
        scenario_id="plumpudding_beach_esperance_whale_carcass_2026_hypothetical_sighting",
        label="Plumpudding Beach Esperance whale carcass sensitivity replay (hypothetical sighting)",
        lat=_PLUMPUDDING_LAT,
        lon=_PLUMPUDDING_LON,
        timestamp=datetime(2026, 5, 29, 7, 10, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        biological_events=[_plumpudding_carcass_event()],
        sighting_reports=[_hypothetical_nearby_sighting()],
        month=5,
        activity_context=None,
        suspected_species=None,
        radius_km=10.0,
        lookback_hours=168,
        expected_warning_band="low",
        tags=["western_australia", "esperance", "whale_carcass", "hypothetical", "sighting_sensitivity"],
    ),
}
