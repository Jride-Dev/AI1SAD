from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.hawaii_water_clarity import (
    HAWAII_WATER_CLARITY_SIGNAL_TYPES,
    HawaiiWaterClarityProvider,
    normalize_static_hawaii_water_clarity_signals,
    provider_health_document,
)
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS
from app.replay.runner import ReplayRunner
from app.replay.scenarios import REPLAY_SCENARIOS
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.explainability_engine import build_explanation
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import hawaii_water_clarity_surveillance_points, score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_static_water_clarity_profiles_cover_oahu_demo_scope():
    provider = HawaiiWaterClarityProvider()
    matches = provider.matching_profiles(lat=21.255, lon=-157.81, radius_km=10)

    assert matches
    assert matches[0]["id"] == "oahu_cromwells_visibility_baseline"
    assert matches[0]["baseline_only"] is True
    assert "NOAA CoastWatch" in matches[0]["preferred_source"]
    assert "PacIOOS" in " ".join(matches[0]["fallback_sources"])


def test_water_clarity_provider_normalizes_public_signal_shape():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)

    assert signals
    sample = signals[0]
    assert sample["signal_type"] in HAWAII_WATER_CLARITY_SIGNAL_TYPES
    assert sample["source"]["provider"] == "hawaii_water_clarity_static"
    assert sample["provider_timestamp"] == sample["timestamp"]
    assert sample["baseline_only"] is True
    assert sample["clarity_class"]
    assert sample["turbidity_class"]
    assert sample["data_freshness"]["status"] in {"fresh", "stale"}
    assert "private_notes" not in str(sample)


def test_water_clarity_alone_does_not_create_high_warning():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.255,
        lon=-157.81,
        hawaii_water_clarity_signals=inputs["hawaii_water_clarity_signals"],
        provider_status=inputs["provider_status"],
    )

    assert warning["warning_band"] == "low"
    assert warning["warning_score"] < 10
    assert warning["signals"]["hawaii_water_clarity_context_score"] <= 1.8


def test_visibility_context_modestly_raises_surveillance_attention():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
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
    assert active["zones"][0]["surveillance_priority_score"] < 25
    assert "hawaii_water_clarity_static" in active["zones"][0]["data_sources_used"]


def test_stacked_visibility_and_activity_outweigh_visibility_alone():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    visibility_only = score_surveillance_zones(
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

    assert stacked["zones"][0]["surveillance_priority_score"] > visibility_only["zones"][0]["surveillance_priority_score"]


def test_static_visibility_freshness_lowers_confidence():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.255,
        lon=-157.81,
        hawaii_water_clarity_signals=inputs["hawaii_water_clarity_signals"],
        provider_status=inputs["provider_status"],
    )

    assert warning["signals"]["baseline_visibility_freshness_confidence_modifier"] == -0.03
    assert "hawaii_water_clarity_static" in warning["data_sources_used"]


def test_private_water_clarity_notes_are_filtered_from_public_alerts():
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
                    "signal_type": "turbidity_context",
                    "expires_at": (now + timedelta(hours=12)).isoformat(),
                    "private_notes": "internal only",
                }
            ],
        },
        now=now,
    )

    assert any(alert["trigger"]["trigger_type"] == "hawaii_water_clarity_context" for alert in alerts)
    assert "private_notes" not in str(alerts)
    assert "internal only" not in str(alerts)


def test_explainability_includes_water_clarity_factors_when_active():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
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

    assert "hawaii_water_clarity_static" in explanation["data_freshness"]
    assert "hawaii_water_clarity_static" in surveillance["zones"][0]["data_sources_used"]
    assert "hawaii_water_clarity_baseline_context" in factors or "visibility_activity_stack_context" in factors


def test_water_clarity_explainability_factor_labels_are_explicit():
    signals = normalize_static_hawaii_water_clarity_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    points, signal_types, factors, confidence_penalty = hawaii_water_clarity_surveillance_points(
        inputs["hawaii_water_clarity_signals"],
        activity_context="surfing",
        biological_events=[],
        human_exposure_index=None,
        verified_sighting_count=0,
    )
    factor_names = {factor["factor"] for factor in factors}

    assert points <= 6
    assert confidence_penalty == -0.04
    assert "water_clarity_context" in signal_types
    assert {
        "water_clarity_context",
        "turbidity_context",
        "sediment_runoff_visibility_context",
        "surf_zone_visibility_context",
        "visibility_activity_stack_context",
        "baseline_visibility_freshness",
    } <= factor_names


def test_cromwells_replay_remains_timeline_safe_and_bounded_with_visibility_context():
    pre = REPLAY_SCENARIOS["cromwells_beach_hawaii_2026_pre_surfing"]
    runner = ReplayRunner()
    result = runner.run_scenario(pre)

    assert result.error is None
    assert pre.sighting_reports == []
    assert pre.hawaii_water_clarity_signals
    assert result.warning["warning_band"] == "low"
    assert result.warning["warning_score"] < 25
    assert result.warning["signals"]["hawaii_water_clarity_context_score"] <= 1.8


def test_water_clarity_provider_health_and_decay_params():
    health = provider_health_document(generated_signals=5)

    assert health["_id"] == "hawaii_water_clarity_static"
    assert health["mode"] == "static_manual_offline"
    assert SIGNAL_TYPE_DECAY_PARAMS["turbidity_context"]["half_life_hours"] == 1440.0
