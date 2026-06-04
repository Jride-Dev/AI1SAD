from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.hawaii_tide_current import (
    HAWAII_TIDE_CURRENT_SIGNAL_TYPES,
    HawaiiTideCurrentProvider,
    normalize_static_hawaii_tide_current_signals,
    provider_health_document,
)
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS
from app.replay.runner import ReplayRunner
from app.replay.scenarios import REPLAY_SCENARIOS
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.explainability_engine import build_explanation
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import hawaii_tide_current_surveillance_points, score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_static_tide_current_profiles_prioritize_south_shore_oahu_roms():
    provider = HawaiiTideCurrentProvider()
    matches = provider.matching_profiles(lat=21.255, lon=-157.81, radius_km=10)

    assert matches
    assert matches[0]["preferred_source"] == "PacIOOS South Shore Oahu ROMS"
    assert "PacIOOS Oahu ROMS" in matches[0]["fallback_sources"]
    assert "PacIOOS Main Hawaiian Islands ROMS" in matches[0]["fallback_sources"]
    assert "NOAA CO-OPS" in matches[0]["supporting_station_source"]
    assert matches[0]["baseline_only"] is True


def test_tide_current_provider_normalizes_public_signal_shape():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)

    assert signals
    sample = signals[0]
    assert sample["signal_type"] in HAWAII_TIDE_CURRENT_SIGNAL_TYPES
    assert sample["source"]["provider"] == "hawaii_tide_current_static"
    assert sample["provider_timestamp"] == sample["timestamp"]
    assert sample["baseline_only"] is True
    assert sample["preferred_source"] == "PacIOOS South Shore Oahu ROMS"
    assert sample["nearshore_model_resolution"] == "preferred_south_shore_nearshore"
    assert sample["forecast_freshness"] == "static_not_live"
    assert sample["station_coverage_gap"] == "station_support_not_microchannel_observation"
    assert sample["regional_fallback_used"] is False
    assert sample["data_freshness"]["status"] in {"fresh", "stale"}
    assert "private_notes" not in str(sample)


def test_tide_current_alone_does_not_create_high_warning():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.255,
        lon=-157.81,
        hawaii_tide_current_signals=inputs["hawaii_tide_current_signals"],
        provider_status=inputs["provider_status"],
    )

    assert warning["warning_band"] == "low"
    assert warning["warning_score"] < 10
    assert warning["signals"]["hawaii_tide_current_context_score"] <= 2.5


def test_channel_flow_baseline_modestly_raises_surveillance_attention():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    baseline = score_surveillance_zones(lat=21.255, lon=-157.81, radius_km=8, mission_type="drone", lookback_hours=72)
    active = score_surveillance_zones(
        lat=21.255,
        lon=-157.81,
        radius_km=8,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs=inputs,
    )

    assert active["zones"][0]["surveillance_priority_score"] > baseline["zones"][0]["surveillance_priority_score"]
    assert any(f["factor"] == "channel_flow_context" for f in active["zones"][0]["dominant_factors"])
    assert active["zones"][0]["surveillance_priority_score"] < 30


def test_stacked_current_and_activity_outweigh_water_movement_alone():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    water_only = score_surveillance_zones(
        lat=21.255,
        lon=-157.81,
        radius_km=8,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs=inputs,
    )
    stacked = score_surveillance_zones(
        lat=21.255,
        lon=-157.81,
        radius_km=8,
        mission_type="drone",
        lookback_hours=72,
        activity_context="surfing",
        warning_inputs=inputs,
        profiles=REGIONAL_RISK_PROFILES,
    )

    assert stacked["zones"][0]["surveillance_priority_score"] > water_only["zones"][0]["surveillance_priority_score"]


def test_static_tide_current_freshness_lowers_confidence():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.255,
        lon=-157.81,
        hawaii_tide_current_signals=inputs["hawaii_tide_current_signals"],
        provider_status=inputs["provider_status"],
    )

    assert warning["signals"]["baseline_tide_current_freshness_confidence_modifier"] == -0.03
    assert "hawaii_tide_current_static" in warning["data_sources_used"]


def test_private_tide_current_notes_are_filtered_from_public_alerts():
    now = datetime.now(timezone.utc)
    alerts = evaluate_alerts(
        {
            "lat": 21.255,
            "lon": -157.81,
            "warning_score": 12,
            "surveillance_priority_score": 66,
            "activity_hazard_score": 46,
            "signals": [
                {
                    "visibility": "public",
                    "signal_type": "channel_flow_context",
                    "expires_at": (now + timedelta(hours=12)).isoformat(),
                    "private_notes": "internal only",
                }
            ],
        },
        now=now,
    )

    assert any(alert["trigger"]["trigger_type"] == "hawaii_tide_current_context" for alert in alerts)
    assert "private_notes" not in str(alerts)
    assert "internal only" not in str(alerts)


def test_explainability_includes_tide_current_factors_when_active():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    surveillance = score_surveillance_zones(
        lat=21.255,
        lon=-157.81,
        radius_km=8,
        mission_type="drone",
        lookback_hours=72,
        activity_context="surfing",
        warning_inputs=inputs,
    )
    explanation = build_explanation(surveillance, output_type="surveillance")
    factors = {item["factor"] for item in explanation["dominant_factors"]}

    assert "hawaii_tide_current_static" in explanation["data_freshness"]
    assert "hawaii_tide_current_static" in surveillance["zones"][0]["data_sources_used"]
    assert "hawaii_tide_current_baseline_context" in factors or "channel_flow_context" in factors


def test_tide_current_explainability_factor_labels_are_explicit():
    signals = normalize_static_hawaii_tide_current_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    points, signal_types, factors, confidence_penalty = hawaii_tide_current_surveillance_points(
        inputs["hawaii_tide_current_signals"],
        activity_context="surfing",
        biological_events=[],
        human_exposure_index=None,
        verified_sighting_count=0,
    )
    factor_names = {factor["factor"] for factor in factors}

    assert points <= 14
    assert confidence_penalty == -0.03
    assert "tide_state_context" in signal_types
    assert {
        "tide_state_context",
        "channel_flow_context",
        "current_speed_context",
        "current_convergence_context",
        "nearshore_model_resolution",
        "forecast_freshness",
        "station_coverage_gap",
    } <= factor_names
    assert "regional_fallback_used" not in factor_names


def test_cromwells_replay_remains_timeline_safe_and_bounded_with_tide_current_context():
    pre = REPLAY_SCENARIOS["cromwells_beach_hawaii_2026_pre_surfing"]
    post = REPLAY_SCENARIOS["cromwells_beach_hawaii_2026_post_update"]
    runner = ReplayRunner()
    pre_result = runner.run_scenario(pre)
    post_result = runner.run_scenario(post)

    assert pre_result.error is None
    assert post_result.error is None
    assert pre.sighting_reports == []
    assert pre_result.warning["warning_band"] == "low"
    assert pre_result.warning["warning_score"] < 25
    assert pre.hawaii_tide_current_signals
    assert post_result.surveillance["zones"][0]["surveillance_priority_score"] > pre_result.surveillance["zones"][0]["surveillance_priority_score"]


def test_tide_current_provider_health_and_decay_params():
    health = provider_health_document(generated_signals=7)

    assert health["_id"] == "hawaii_tide_current_static"
    assert health["mode"] == "static_manual_offline"
    assert SIGNAL_TYPE_DECAY_PARAMS["channel_flow_context"]["half_life_hours"] == 1440.0
