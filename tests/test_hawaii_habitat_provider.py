from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.hawaii_habitat import (
    HAWAII_HABITAT_SIGNAL_TYPES,
    STATIC_HAWAII_HABITAT_PROFILES,
    normalize_static_hawaii_habitat_signals,
    provider_health_document,
)
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.explainability_engine import build_explanation
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_hawaii_habitat_profiles_cover_oahu_demo_scope():
    profile_ids = {profile["id"] for profile in STATIC_HAWAII_HABITAT_PROFILES}
    assert "oahu_cromwells_diamond_head_baseline" in profile_ids
    assert "oahu_kaikoo_hale_mano_channel_baseline" in profile_ids
    assert "oahu_waikiki_ala_moana_baseline" in profile_ids
    assert "oahu_reef_channel_demo_baseline" in profile_ids
    assert "oahu_shallow_reef_edge_demo_baseline" in profile_ids
    assert "oahu_sandy_bottom_quiet_day_baseline" in profile_ids
    assert "reef_channel_habitat" in HAWAII_HABITAT_SIGNAL_TYPES


def test_habitat_provider_normalizes_static_baseline_signals():
    signals = normalize_static_hawaii_habitat_signals(lat=21.255, lon=-157.81, radius_km=8)
    assert signals
    sample = signals[0]
    assert sample["source"]["provider"] == "hawaii_habitat_static"
    assert sample["baseline_only"] is True
    assert sample["habitat_profile_id"]
    assert sample["data_freshness"]["status"] in {"stale", "expired"}


def test_habitat_alone_does_not_create_high_warning():
    signals = normalize_static_hawaii_habitat_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.255,
        lon=-157.81,
        hawaii_habitat_signals=inputs["hawaii_habitat_signals"],
        provider_status=inputs["provider_status"],
    )
    assert warning["warning_band"] == "low"
    assert warning["warning_score"] < 20


def test_reef_channel_baseline_modestly_raises_surveillance_attention():
    signals = normalize_static_hawaii_habitat_signals(lat=21.255, lon=-157.81, radius_km=8)
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
    assert any(f["factor"] == "reef_channel_context" for f in active["zones"][0]["dominant_factors"])


def test_stacked_channel_and_activity_outweigh_habitat_alone():
    signals = normalize_static_hawaii_habitat_signals(lat=21.255, lon=-157.81, radius_km=8)
    inputs = warning_inputs_from_signals(signals)
    habitat_only = score_surveillance_zones(
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
    assert stacked["zones"][0]["surveillance_priority_score"] > habitat_only["zones"][0]["surveillance_priority_score"]


def test_quiet_sandy_bottom_baseline_has_low_influence():
    signals = normalize_static_hawaii_habitat_signals(lat=21.27, lon=-157.85, radius_km=3)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(
        lat=21.27,
        lon=-157.85,
        hawaii_habitat_signals=inputs["hawaii_habitat_signals"],
        provider_status=inputs["provider_status"],
    )
    assert warning["signals"]["hawaii_habitat_context_score"] <= 3.5
    assert warning["warning_band"] == "low"


def test_private_habitat_notes_are_filtered_from_public_outputs():
    now = datetime.now(timezone.utc)
    alerts = evaluate_alerts(
        {
            "lat": 21.255,
            "lon": -157.81,
            "warning_score": 8,
            "surveillance_priority_score": 66,
            "activity_hazard_score": 46,
            "signals": [
                {
                    "visibility": "public",
                    "signal_type": "reef_channel_habitat",
                    "expires_at": (now + timedelta(hours=12)).isoformat(),
                    "private_notes": "internal only",
                }
            ],
        },
        now=now,
    )
    assert any(alert["trigger"]["trigger_type"] == "hawaii_habitat_context" for alert in alerts)
    assert "private_notes" not in str(alerts)
    assert "restricted" not in str(alerts)


def test_explainability_includes_habitat_factors_when_active():
    signals = normalize_static_hawaii_habitat_signals(lat=21.255, lon=-157.81, radius_km=8)
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
    assert "hawaii_habitat_static" in explanation["data_freshness"]
    assert "hawaii_habitat_static" in surveillance["zones"][0]["data_sources_used"]
    assert "hawaii_habitat_baseline_context" in factors or "reef_channel_context" in factors


def test_habitat_provider_health_and_decay_params():
    health = provider_health_document(generated_signals=6)
    assert health["_id"] == "hawaii_habitat_static"
    assert SIGNAL_TYPE_DECAY_PARAMS["reef_channel_habitat"]["half_life_hours"] == 1440.0
