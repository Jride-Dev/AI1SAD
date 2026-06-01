from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.kelp_forest import (
    KELP_SIGNAL_TYPES,
    STATIC_KELP_FOREST_PROFILES,
    normalize_static_kelp_forest_signals,
    provider_health_document,
)
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.explainability_engine import build_explanation
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_static_profiles_cover_required_demo_regions():
    profile_ids = {profile["profile_id"] for profile in STATIC_KELP_FOREST_PROFILES}

    assert "central_california_white_shark_kelp_demo" in profile_ids
    assert "monterey_bay_central_coast_kelp_demo" in profile_ids
    assert "false_bay_seal_island_kelp_context" in profile_ids
    assert "western_australia_reef_kelp_context" in profile_ids
    assert "golden_rule_kelp_bed_demo" in profile_ids
    assert {
        "kelp_forest_presence",
        "kelp_density_context",
        "kelp_edge_habitat",
        "kelp_prey_overlap",
        "white_shark_kelp_hunting_context",
    } <= KELP_SIGNAL_TYPES


def test_kelp_provider_normalizes_public_signal_shape_with_stale_freshness():
    signals = normalize_static_kelp_forest_signals(lat=36.95, lon=-122.05, radius_km=5)

    assert signals
    signal = next(item for item in signals if item["signal_type"] == "kelp_edge_habitat")
    assert signal["source"]["provider"] == "kelp_forest_static"
    assert signal["location"]["geo"]["type"] == "Point"
    assert signal["density_class"] == "optimal_edge"
    assert signal["pinniped_presence"] is True
    assert signal["pack_id"]
    assert signal["data_freshness"]["status"] == "stale"
    assert signal["profile_id"] == "central_california_white_shark_kelp_demo"


def test_kelp_signals_feed_broker_inputs_without_private_notes():
    signals = normalize_static_kelp_forest_signals(lat=36.95, lon=-122.05, radius_km=5)
    inputs = warning_inputs_from_signals(signals)

    assert inputs["kelp_habitat_signals"]
    assert inputs["provider_status"]["kelp_forest_static"] == "stale"
    assert "private_notes" not in str(inputs)
    assert "restricted" not in str(inputs)


def test_kelp_alone_does_not_create_high_warning():
    signals = normalize_static_kelp_forest_signals(lat=36.95, lon=-122.05, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(lat=36.95, lon=-122.05, kelp_habitat_signals=inputs["kelp_habitat_signals"])

    assert warning["warning_score"] < 15
    assert warning["warning_band"] == "low"
    assert warning["signals"]["kelp_forest_context_score"] <= 4


def test_optimal_kelp_edge_with_pinnipeds_raises_surveillance_priority():
    signals = normalize_static_kelp_forest_signals(lat=36.95, lon=-122.05, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    baseline = score_surveillance_zones(lat=36.95, lon=-122.05, radius_km=5, mission_type="drone", lookback_hours=72)
    kelp = score_surveillance_zones(
        lat=36.95,
        lon=-122.05,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        activity_context="surfing",
        suspected_species="white shark",
        profiles=REGIONAL_RISK_PROFILES,
        warning_inputs=inputs,
    )

    zone = kelp["zones"][0]
    assert zone["surveillance_priority_score"] > baseline["zones"][0]["surveillance_priority_score"]
    assert any(factor["factor"] == "kelp_forest_surveillance_context" for factor in zone["dominant_factors"])
    kelp_factor = next(item for item in zone["dominant_factors"] if item["factor"] == "kelp_forest_surveillance_context")
    assert kelp_factor["optimal_kelpedge_score"] > 0
    assert zone["recommended_pattern"] == "kelp-edge expanding grid"


def test_dense_kelp_affects_confidence_without_automatic_high_danger():
    signals = normalize_static_kelp_forest_signals(lat=36.8, lon=-122.2, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(lat=36.8, lon=-122.2, kelp_habitat_signals=inputs["kelp_habitat_signals"])

    assert warning["warning_score"] < 15
    assert warning["warning_band"] == "low"
    assert warning["signals"]["kelp_visibility_confidence_modifier"] == -0.04


def test_sparse_kelp_has_low_influence():
    signals = normalize_static_kelp_forest_signals(lat=-31.98, lon=115.51, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(lat=-31.98, lon=115.51, kelp_habitat_signals=inputs["kelp_habitat_signals"])
    surveillance = score_surveillance_zones(
        lat=-31.98,
        lon=115.51,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs=inputs,
    )

    assert warning["signals"]["kelp_forest_context_score"] <= 1
    factor = next(item for item in surveillance["zones"][0]["dominant_factors"] if item["factor"] == "kelp_forest_surveillance_context")
    assert factor["points"] <= 3
    assert factor["optimal_kelpedge_score"] == 0


def test_kelp_human_activity_overlap_increases_operational_attention():
    signals = normalize_static_kelp_forest_signals(lat=36.62, lon=-121.92, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    baseline = score_surveillance_zones(lat=36.62, lon=-121.92, radius_km=5, mission_type="drone", lookback_hours=72, warning_inputs=inputs)
    active = score_surveillance_zones(
        lat=36.62,
        lon=-121.92,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        activity_context="diving",
        suspected_species="white shark",
        warning_inputs=inputs,
    )

    assert active["zones"][0]["surveillance_priority_score"] > baseline["zones"][0]["surveillance_priority_score"]
    assert "kelp_human_activity_overlap" in str(active["zones"][0]["dominant_factors"])


def test_alerts_use_kelp_only_when_stacked_and_hide_internal_notes():
    now = datetime.now(timezone.utc)
    weak = evaluate_alerts(
        {
            "lat": 36.95,
            "lon": -122.05,
            "warning_score": 4,
            "surveillance_priority_score": 20,
            "activity_hazard_score": 0,
            "signals": [{"visibility": "public", "signal_type": "kelp_edge_habitat", "expires_at": (now + timedelta(hours=12)).isoformat()}],
        },
        now=now,
    )
    stacked = evaluate_alerts(
        {
            "lat": 36.95,
            "lon": -122.05,
            "warning_score": 8,
            "surveillance_priority_score": 65,
            "activity_hazard_score": 48,
            "confidence": 0.7,
            "signals": [
                {
                    "visibility": "public",
                    "signal_type": "kelp_edge_habitat",
                    "expires_at": (now + timedelta(hours=12)).isoformat(),
                    "private_notes": "hide me",
                }
            ],
        },
        now=now,
    )

    assert weak == []
    assert any(alert["trigger"]["trigger_type"] == "kelp_habitat_context" for alert in stacked)
    assert "private_notes" not in str(stacked)
    assert "restricted" not in str(stacked)


def test_explanation_includes_kelp_factors_when_active():
    signals = normalize_static_kelp_forest_signals(lat=36.95, lon=-122.05, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    surveillance = score_surveillance_zones(
        lat=36.95,
        lon=-122.05,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        activity_context="surfing",
        suspected_species="white shark",
        warning_inputs=inputs,
    )
    explanation = build_explanation(surveillance, output_type="surveillance")

    assert any(item["factor"] == "kelp_forest_surveillance_context" for item in explanation["dominant_factors"])
    assert "kelp" in explanation["recommended_surveillance_pattern"]


def test_kelp_provider_health_and_decay_params():
    health = provider_health_document(generated_signals=5)

    assert health["_id"] == "kelp_forest_static"
    assert health["status"] == "healthy"
    assert health["mode"] == "static_manual_offline"
    assert SIGNAL_TYPE_DECAY_PARAMS["kelp_edge_habitat"]["half_life_hours"] == 720.0
