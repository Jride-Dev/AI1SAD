from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.noaa_coastwatch import normalize_offline_sst_records
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.alert_engine import evaluate_alerts
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


def sst_records(*, temperature_c: float = 28.0, anomaly_c: float = 1.5, hours_old: int = 1):
    observed = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    return [
        {
            "temperature_c": temperature_c,
            "anomaly_c": anomaly_c,
            "timestamp": observed.isoformat(),
            "expires_at": (observed + timedelta(hours=48)).isoformat(),
            "confidence": 0.82,
            "dataset": "mock_sst",
        }
    ]


def test_offline_sst_adapter_normalizes_signal_shape():
    signals = normalize_offline_sst_records(sst_records(), lat=27.7, lon=-80.2)
    types = {signal["signal_type"] for signal in signals}

    assert {"sea_surface_temperature", "sst_anomaly", "ocean_temperature_context"} <= types
    for signal in signals:
        assert signal["source"]["provider"] == "noaa_coastwatch"
        assert signal["source"]["dataset"] == "mock_sst"
        assert signal["location"]["geo"]["coordinates"] == [-80.2, 27.7]
        assert signal["provider_timestamp"]
        assert signal["data_freshness"]["status"] == "fresh"
        assert signal["confidence"] > 0
        assert signal["temperature_c"] == 28
        assert signal["anomaly_c"] == 1.5

    sst = next(signal for signal in signals if signal["signal_type"] == "sea_surface_temperature")
    anomaly = next(signal for signal in signals if signal["signal_type"] == "sst_anomaly")
    context = next(signal for signal in signals if signal["signal_type"] == "ocean_temperature_context")
    assert sst["temperature_c"] == 28
    assert anomaly["anomaly_c"] == 1.5
    assert context["temperature_c"] == 28
    assert context["anomaly_c"] == 1.5


def test_sst_signals_feed_warning_inputs():
    signals = normalize_offline_sst_records(sst_records(temperature_c=27, anomaly_c=1), lat=27.7, lon=-80.2)
    inputs = warning_inputs_from_signals(signals)

    assert inputs["sea_surface_temp_c"] == 27
    assert inputs["sst_anomaly_c"] == 1
    assert inputs["data_freshness"]["noaa_coastwatch"]["status"] == "fresh"


def test_region_specific_sst_context_weights_supported_regions():
    cases = [
        (27.7, -80.2, 28.0, "florida"),
        (-31.95, 115.86, 20.0, "western_australia"),
        (21.3, -157.8, 26.0, "hawaii"),
        (20.5, 38.5, 30.0, "red_sea"),
    ]
    for lat, lon, temp, region in cases:
        result = calculate_warning(lat=lat, lon=lon, sea_surface_temp_c=temp, sst_anomaly_c=1.0, profiles=REGIONAL_RISK_PROFILES)
        assert result["regional_profile"]["region_key"] == region
        assert "regional_sst_species_context" in {factor["factor"] for factor in result["dominant_factors"]}
        assert result["signals"]["sst_score"] > 0


def test_sst_alone_does_not_create_high_warning_state():
    result = calculate_warning(lat=27.7, lon=-80.2, sea_surface_temp_c=28.0, sst_anomaly_c=1.0, profiles=REGIONAL_RISK_PROFILES)

    assert result["warning_score"] < 25
    assert result["warning_band"] == "low"


def test_stale_sst_degrades_confidence_without_crashing():
    signals = normalize_offline_sst_records(sst_records(temperature_c=28, anomaly_c=1, hours_old=40), lat=27.7, lon=-80.2)
    inputs = warning_inputs_from_signals(signals)
    result = calculate_warning(
        lat=27.7,
        lon=-80.2,
        sea_surface_temp_c=inputs["sea_surface_temp_c"],
        sst_anomaly_c=inputs["sst_anomaly_c"],
        profiles=REGIONAL_RISK_PROFILES,
        provider_status=inputs["provider_status"],
    )

    assert inputs["data_freshness"]["noaa_coastwatch"]["status"] == "stale"
    assert "noaa_coastwatch:stale" in result["missing_data_sources"]
    assert result["confidence"] < 0.9


def test_missing_sst_does_not_crash_and_reports_missing_ocean_freshness():
    result = calculate_warning(lat=27.7, lon=-80.2, profiles=REGIONAL_RISK_PROFILES)

    assert result["signals"]["sst_score"] == 0
    assert "ocean_observations" in result["missing_data_sources"]
    assert result["confidence"] < 0.9


def test_surveillance_consumes_sst_context_as_supporting_factor():
    response = score_surveillance_zones(
        lat=-31.95,
        lon=115.86,
        radius_km=10,
        mission_type="drone_search",
        lookback_hours=72,
        activity_context="spearfishing",
        suspected_species="white shark",
        profiles=REGIONAL_RISK_PROFILES,
        reef_features=[{"visibility": "public", "feature_type": "reef"}],
        warning_inputs={"sea_surface_temp_c": 20.0, "sst_anomaly_c": 0.5, "provider_status": {}},
    )

    factors = response["zones"][0]["dominant_factors"]
    assert any(factor["factor"] in {"regional_sst_species_context", "wa_white_shark_reef_spearfishing_context"} for factor in factors)
    assert response["zones"][0]["warning_score"] > 0


def test_alert_engine_uses_sst_context_only_as_supporting_surveillance_signal():
    signals = normalize_offline_sst_records(sst_records(temperature_c=20, anomaly_c=0.5), lat=-31.95, lon=115.86)
    alerts = evaluate_alerts(
        {
            "lat": -31.95,
            "lon": 115.86,
            "warning_score": 20,
            "surveillance_priority_score": 65,
            "activity_hazard_score": 0,
            "signals": signals,
            "confidence": 0.7,
        }
    )

    assert any(alert["alert_type"] == "surveillance_priority" for alert in alerts)
