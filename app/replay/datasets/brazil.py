from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.replay.scenarios import ReplayScenario


RECIFE_TZ = timezone(timedelta(hours=-3))

_PIEDADE_LAT = -8.171
_PIEDADE_LON = -34.914
_BOA_VIAGEM_LAT = -8.126
_BOA_VIAGEM_LON = -34.899


def _piedade_recent_interaction_for_boa_viagem() -> dict:
    return {
        "visibility": "public",
        "source": "CEMIT preliminary public assessment / incident reporting",
        "confidence": "source_attributed_preliminary",
        "observed_at": "2026-05-31T13:40:00-03:00",
        "location": {"geo": {"type": "Point", "coordinates": [_PIEDADE_LON, _PIEDADE_LAT]}},
        "location_name": "Piedade Beach, Jaboatao dos Guararapes, Greater Recife, Pernambuco, Brazil",
        "victim_context": "bather, age 11",
        "outcome": "serious injuries with left-leg amputation",
        "source_attributed_species_assessment": {
            "assessing_body": "CEMIT",
            "classification_status": "preliminary_source_attributed",
            "taxon": "adult bull shark",
            "portuguese_source_term": "tubarão-cabeça-chata",
            "estimated_length_m": 2.5,
            "independent_taxonomy_verified": False,
            "model_input_for_strict_preincident": False,
        },
        "same_individual_assumption": False,
    }


SCENARIOS = {
    "piedade_beach_recife_2026_pre_incident": ReplayScenario(
        scenario_id="piedade_beach_recife_2026_pre_incident",
        label="Piedade Beach Recife May 31 2026 strict pre-incident replay",
        lat=_PIEDADE_LAT,
        lon=_PIEDADE_LON,
        timestamp=datetime(2026, 5, 31, 13, 35, 0, tzinfo=RECIFE_TZ),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        month=5,
        activity_context="swimming",
        suspected_species=None,
        reef_habitat=True,
        dropoff_habitat=False,
        reef_feature_name="Greater Recife reef-barrier and nearshore channel baseline context",
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        use_regional_profiles=False,
        tags=["brazil", "greater_recife", "piedade", "pre_incident", "timeline_strict"],
    ),
    "piedade_beach_recife_2026_quiet_day": ReplayScenario(
        scenario_id="piedade_beach_recife_2026_quiet_day",
        label="Piedade Beach Recife May 31 2026 quiet-day comparison",
        lat=_PIEDADE_LAT,
        lon=_PIEDADE_LON,
        timestamp=datetime(2026, 5, 31, 13, 35, 0, tzinfo=RECIFE_TZ),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        month=5,
        activity_context="swimming",
        suspected_species=None,
        reef_habitat=True,
        dropoff_habitat=False,
        reef_feature_name="Greater Recife reef-barrier and nearshore channel baseline context",
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        use_regional_profiles=False,
        tags=["brazil", "greater_recife", "piedade", "quiet_day", "timeline_strict"],
    ),
    "boa_viagem_recife_2026_pre_incident": ReplayScenario(
        scenario_id="boa_viagem_recife_2026_pre_incident",
        label="Boa Viagem Recife June 1 2026 strict pre-incident replay",
        lat=_BOA_VIAGEM_LAT,
        lon=_BOA_VIAGEM_LON,
        timestamp=datetime(2026, 6, 1, 15, 5, 0, tzinfo=RECIFE_TZ),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        recent_interactions=[_piedade_recent_interaction_for_boa_viagem()],
        month=6,
        activity_context="swimming",
        suspected_species=None,
        reef_habitat=True,
        dropoff_habitat=False,
        reef_feature_name="Acaiaca / Padre Bernardino Pessoa reef-barrier and nearshore channel corridor baseline context",
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        use_regional_profiles=False,
        tags=["brazil", "greater_recife", "boa_viagem", "pre_incident", "timeline_strict", "incident_cluster"],
    ),
    "boa_viagem_recife_2026_quiet_day": ReplayScenario(
        scenario_id="boa_viagem_recife_2026_quiet_day",
        label="Boa Viagem Recife June 1 2026 quiet-day comparison",
        lat=_BOA_VIAGEM_LAT,
        lon=_BOA_VIAGEM_LON,
        timestamp=datetime(2026, 6, 1, 15, 5, 0, tzinfo=RECIFE_TZ),
        rainfall_72h_mm=None,
        river_mouth_distance_km=None,
        sea_surface_temp_c=None,
        sst_anomaly_c=None,
        vessel_activity_index=None,
        human_exposure_index=None,
        month=6,
        activity_context="swimming",
        suspected_species=None,
        reef_habitat=True,
        dropoff_habitat=False,
        reef_feature_name="Acaiaca / Padre Bernardino Pessoa reef-barrier and nearshore channel corridor baseline context",
        radius_km=8.0,
        lookback_hours=72,
        expected_warning_band="low",
        use_regional_profiles=False,
        tags=["brazil", "greater_recife", "boa_viagem", "quiet_day", "timeline_strict"],
    ),
}
