from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.vessel_fishing import (
    STATIC_VESSEL_FISHING_SIGNALS,
    VESSEL_FISHING_SIGNAL_TYPES,
    default_duration_hours,
    normalize_static_vessel_fishing_signals,
    provider_health_document,
)
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS, apply_decay_to_signals
from app.services.alert_engine import evaluate_alerts
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_static_vessel_examples_cover_required_regions():
    signal_ids = {signal["signal_id"] for signal in STATIC_VESSEL_FISHING_SIGNALS}

    assert "florida_inlet_pier_recreational_fishing" in signal_ids
    assert "wa_reef_spearfishing_context" in signal_ids
    assert "red_sea_liveaboard_dive_corridor" in signal_ids
    assert "south_africa_fishing_seal_colony_coastline" in signal_ids
    assert "hawaii_nearshore_recreational_fishing" in signal_ids
    assert {
        "vessel_activity",
        "fishing_activity",
        "commercial_fishing_pressure",
        "recreational_fishing_pressure",
        "spearfishing_activity",
        "pier_fishing_pressure",
        "marina_boat_pressure",
        "dive_boat_activity",
        "liveaboard_activity",
    } <= VESSEL_FISHING_SIGNAL_TYPES


def test_vessel_fishing_provider_normalizes_signal_shape():
    signals = normalize_static_vessel_fishing_signals(lat=-31.983, lon=115.515, radius_km=5)

    assert signals
    signal = signals[0]
    assert signal["signal_type"] == "spearfishing_activity"
    assert signal["activity_type"] == "spearfishing_activity"
    assert signal["source"]["provider"] == "vessel_fishing_static"
    assert signal["provider_timestamp"] == signal["timestamp"]
    assert signal["location"]["geo"]["type"] == "Point"
    assert signal["confidence"] > 0
    assert signal["data_freshness"]["status"] == "fresh"
    assert signal["signal_id"] == "wa_reef_spearfishing_context"
    assert signal["pack_id"] == "western_australia"
    assert signal["duration_hours"] == 24


def test_vessel_fishing_signals_feed_warning_inputs():
    signals = normalize_static_vessel_fishing_signals(lat=27.7, lon=-80.2, radius_km=5)
    inputs = warning_inputs_from_signals(signals)

    assert inputs["vessel_activity_index"] > 0.7
    assert inputs["vessel_fishing_signals"]
    assert inputs["vessel_fishing_signals"][0]["signal_type"] == "pier_fishing_pressure"
    assert inputs["provider_status"]["vessel_fishing_static"] == "ok"


def test_vessel_activity_alone_does_not_create_high_warning():
    result = calculate_warning(lat=27.7, lon=-80.2, vessel_activity_index=1.0)

    assert result["signals"]["fishing_vessel_activity_score"] == 10
    assert result["warning_score"] < 25
    assert result["warning_band"] in {"low", "moderate"}


def test_spearfishing_signal_raises_surveillance_more_than_general_warning():
    signals = normalize_static_vessel_fishing_signals(lat=-31.983, lon=115.515, radius_km=5)
    inputs = warning_inputs_from_signals(signals)
    warning = calculate_warning(lat=-31.983, lon=115.515, vessel_activity_index=inputs["vessel_activity_index"])
    surveillance = score_surveillance_zones(
        lat=-31.983,
        lon=115.515,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        activity_context="spearfishing",
        suspected_species="white shark",
        reef_features=[{"visibility": "public", "feature_type": "reef"}],
        warning_inputs=inputs,
    )
    zone = surveillance["zones"][0]

    assert warning["warning_score"] < 25
    assert zone["surveillance_priority_score"] > warning["warning_score"]
    assert any(factor["factor"] == "vessel_fishing_surveillance_context" for factor in zone["dominant_factors"])


def test_fishing_biological_exposure_stack_raises_surveillance_priority():
    now = datetime.now(timezone.utc).isoformat()
    fishing = [{"visibility": "public", "signal_type": "fishing_activity", "confidence": 0.9, "value": 0.9, "observed_at": now}]
    baseline = score_surveillance_zones(
        lat=27.7,
        lon=-80.2,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs={"vessel_fishing_signals": fishing, "provider_status": {}},
    )
    stacked = score_surveillance_zones(
        lat=27.7,
        lon=-80.2,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs={
            "vessel_fishing_signals": fishing,
            "biological_events": [{"visibility": "public", "event_type": "baitfish_presence", "observed_at": now, "confidence": 0.8, "value": 0.9}],
            "human_exposure_index": 0.9,
            "provider_status": {},
        },
    )

    assert stacked["zones"][0]["surveillance_priority_score"] > baseline["zones"][0]["surveillance_priority_score"]
    factors = stacked["zones"][0]["dominant_factors"]
    assert any("fishing_biological_exposure_stack" in factor.get("contexts", []) for factor in factors)


def test_vessel_fishing_expiration_windows_and_decay_types():
    assert default_duration_hours("spearfishing_activity") == 24
    assert default_duration_hours("pier_fishing_pressure") == 168
    assert default_duration_hours("liveaboard_activity") == 72
    assert SIGNAL_TYPE_DECAY_PARAMS["spearfishing_activity"]["half_life_hours"] == 8.0
    assert SIGNAL_TYPE_DECAY_PARAMS["pier_fishing_pressure"]["half_life_hours"] == 72.0

    stale = datetime.now(timezone.utc) - timedelta(hours=80)
    decayed = apply_decay_to_signals([{"signal_type": "spearfishing_activity", "timestamp": stale, "value": 1.0}])
    assert decayed == []


def test_alerts_consume_public_vessel_fishing_signals_without_private_leakage():
    now = datetime.now(timezone.utc)
    alerts = evaluate_alerts(
        {
            "lat": -31.983,
            "lon": 115.515,
            "warning_score": 10,
            "surveillance_priority_score": 62,
            "activity_hazard_score": 30,
            "confidence": 0.7,
            "signals": [
                {
                    "visibility": "public",
                    "signal_type": "spearfishing_activity",
                    "timestamp": now.isoformat(),
                    "expires_at": (now + timedelta(hours=4)).isoformat(),
                    "private_notes": "hide me",
                },
                {
                    "visibility": "private",
                    "signal_type": "fishing_activity",
                    "timestamp": now.isoformat(),
                    "expires_at": (now + timedelta(hours=4)).isoformat(),
                    "private_notes": "restricted",
                },
            ],
        },
        now=now,
    )

    assert any(alert["trigger"]["trigger_type"] == "vessel_fishing_context" for alert in alerts)
    assert "private_notes" not in str(alerts)
    assert "restricted" not in str(alerts)


def test_provider_health_shape():
    health = provider_health_document(generated_signals=4)

    assert health["_id"] == "vessel_fishing_static"
    assert health["provider"] == "vessel_fishing_static"
    assert health["status"] == "healthy"
    assert health["records_ingested"] == 4
    assert health["mode"] == "static_manual_offline"
