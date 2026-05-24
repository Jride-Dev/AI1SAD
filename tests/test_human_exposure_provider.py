from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.human_exposure import HUMAN_EXPOSURE_PROFILES, normalize_static_human_exposure, provider_health_document
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


def test_static_profiles_include_required_beaches():
    names = {profile["name"] for profile in HUMAN_EXPOSURE_PROFILES}
    assert {
        "Clearwater Beach",
        "South Beach Miami",
        "Daytona Beach",
        "New Smyrna Beach",
        "Virginia Beach",
        "Rehoboth Beach",
        "Hampton Beach",
        "Hurghada",
        "Sharm El-Sheikh",
        "Rottnest Island",
    } <= names


def test_human_exposure_provider_normalizes_signal_shape():
    signals = normalize_static_human_exposure(lat=27.977, lon=-82.828, radius_km=5, month=7, weekend=True, holiday=True)
    signal_types = {signal["signal_type"] for signal in signals}

    assert {"human_exposure", "beach_crowd_pressure", "parking_pressure", "tourism_season", "weekend_exposure", "holiday_exposure"} <= signal_types
    for signal in signals:
        assert signal["source"]["provider"] == "human_exposure_static"
        assert signal["source"]["dataset"] == "static_beach_exposure_profiles"
        assert signal["timestamp"]
        assert signal["provider_timestamp"]
        assert signal["location"]["name"] == "Clearwater Beach"
        assert signal["confidence"] > 0
        assert signal["data_freshness"]["status"] == "fresh"
        assert signal["exposure_index"] == signal["value"]
        assert signal["exposure_level"] in {"minimal", "low", "moderate", "high"}
        assert signal["profile_id"] == "clearwater_beach"
        assert signal["pack_id"] == "florida"
        assert signal["source_notes"]


def test_human_exposure_signals_feed_warning_inputs():
    signals = normalize_static_human_exposure(lat=25.782, lon=-80.131, radius_km=5, month=3, weekend=True)
    inputs = warning_inputs_from_signals(signals)

    assert inputs["human_exposure_index"] > 0.8
    assert inputs["data_freshness"]["human_exposure_static"]["status"] == "fresh"


def test_exposure_alone_does_not_create_high_warning_state():
    result = calculate_warning(lat=25.782, lon=-80.131, human_exposure_index=1.0, profiles=REGIONAL_RISK_PROFILES)

    assert result["warning_score"] < 25
    assert result["warning_band"] == "low"
    assert result["signals"]["human_exposure_amplifier_score"] == 0


def test_sst_and_exposure_remain_bounded_without_other_context():
    result = calculate_warning(lat=27.7, lon=-80.2, sea_surface_temp_c=28, sst_anomaly_c=1, human_exposure_index=0.9, profiles=REGIONAL_RISK_PROFILES)

    assert result["warning_score"] < 35
    assert result["warning_band"] in {"low", "moderate"}


def test_exposure_amplifies_rainfall_sst_activity_and_seasonal_context():
    result = calculate_warning(
        lat=27.7,
        lon=-80.2,
        rainfall_72h_mm=80,
        river_mouth_distance_km=2,
        sea_surface_temp_c=28,
        sst_anomaly_c=1,
        human_exposure_index=0.9,
        activity_context="surfing",
        month=7,
        profiles=REGIONAL_RISK_PROFILES,
    )

    assert result["signals"]["human_exposure_amplifier_score"] > 0
    assert result["warning_score"] > calculate_warning(
        lat=27.7,
        lon=-80.2,
        rainfall_72h_mm=80,
        river_mouth_distance_km=2,
        sea_surface_temp_c=28,
        sst_anomaly_c=1,
        human_exposure_index=0.9,
        profiles=REGIONAL_RISK_PROFILES,
    )["warning_score"]


def test_stale_human_exposure_degrades_confidence_without_crashing():
    observed = datetime.now(timezone.utc) - timedelta(hours=40)
    signals = [
        {
            "signal_type": "human_exposure",
            "timestamp": observed,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=4),
            "confidence": 0.6,
            "source": {"provider": "human_exposure_static", "dataset": "test"},
            "risk_relevance": {"score": 0.6, "factors": ["human_exposure"]},
            "visibility": "public",
            "value": 0.9,
        }
    ]
    inputs = warning_inputs_from_signals(signals)
    result = calculate_warning(
        lat=27.7,
        lon=-80.2,
        rainfall_72h_mm=50,
        human_exposure_index=inputs["human_exposure_index"],
        profiles=REGIONAL_RISK_PROFILES,
        provider_status=inputs["provider_status"],
    )

    assert inputs["data_freshness"]["human_exposure_static"]["status"] == "stale"
    assert "human_exposure_static:stale" in result["missing_data_sources"]
    assert result["confidence"] < 0.9


def test_surveillance_consumes_exposure_as_contextual_amplifier():
    with_exposure = score_surveillance_zones(
        lat=27.7,
        lon=-80.2,
        radius_km=10,
        mission_type="drone_search",
        lookback_hours=72,
        activity_context="surfing",
        suspected_species="blacktip shark",
        profiles=REGIONAL_RISK_PROFILES,
        sighting_reports=[{"visibility": "public", "verified": True}],
        warning_inputs={"human_exposure_index": 0.9, "rainfall_72h_mm": 50, "provider_status": {}},
    )
    without_exposure = score_surveillance_zones(
        lat=27.7,
        lon=-80.2,
        radius_km=10,
        mission_type="drone_search",
        lookback_hours=72,
        activity_context="surfing",
        suspected_species="blacktip shark",
        profiles=REGIONAL_RISK_PROFILES,
        sighting_reports=[{"visibility": "public", "verified": True}],
        warning_inputs={"rainfall_72h_mm": 50, "provider_status": {}},
    )

    factors = with_exposure["zones"][0]["dominant_factors"]
    assert any(factor["factor"] == "human_exposure_surveillance_amplifier" for factor in factors)
    assert with_exposure["zones"][0]["surveillance_priority_score"] > without_exposure["zones"][0]["surveillance_priority_score"]


def test_alert_engine_uses_exposure_only_with_other_context():
    signals = normalize_static_human_exposure(lat=27.977, lon=-82.828, radius_km=5, month=7, weekend=True)
    exposure_only = evaluate_alerts({"lat": 27.977, "lon": -82.828, "warning_score": 10, "surveillance_priority_score": 20, "signals": signals})
    with_context = evaluate_alerts({"lat": 27.977, "lon": -82.828, "warning_score": 20, "surveillance_priority_score": 65, "signals": signals})
    with_activity = evaluate_alerts({"lat": 27.977, "lon": -82.828, "warning_score": 20, "activity_hazard_score": 50, "signals": signals})

    assert exposure_only == []
    assert any(alert["alert_type"] == "surveillance_priority" for alert in with_context)
    assert any(alert["alert_type"] == "activity_hazard" for alert in with_activity)


def test_static_provider_health_document_shape():
    health = provider_health_document(generated_signals=3)

    assert health["_id"] == "human_exposure_static"
    assert health["provider"] == "human_exposure_static"
    assert health["status"] == "healthy"
    assert health["last_success"]
    assert health["last_error"] is None
    assert health["records_ingested"] == 3
    assert health["profile_count"] >= 10
    assert health["mode"] == "static_offline"
