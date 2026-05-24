from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import COLLECTIONS, get_database
from app.providers import open_meteo
from app.providers.open_meteo import OpenMeteoProvider
from tests.test_public_api_privacy import FakeDB


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def hourly_payload(hours: int = 72, rain: float = 1.0) -> dict:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours - 1)
    times = [(start + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M") for index in range(hours)]
    return {
        "hourly": {
            "time": times,
            "rain": [rain for _ in range(hours)],
            "temperature_2m": [24.0 for _ in range(hours)],
            "wind_speed_10m": [12.0 for _ in range(hours)],
        }
    }


def make_client(db: FakeDB | None = None) -> tuple[TestClient, FakeDB]:
    fake_db = db or FakeDB()
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_database] = lambda: fake_db
    return TestClient(test_app), fake_db


def test_open_meteo_fetches_and_normalizes_hourly_weather(monkeypatch):
    open_meteo._CACHE.clear()

    def fake_urlopen(_url, timeout=10):
        return FakeResponse(hourly_payload(rain=2.0))

    monkeypatch.setattr(open_meteo, "urlopen", fake_urlopen)
    provider = OpenMeteoProvider()
    weather = provider.fetch_recent_weather(lat=27.7, lon=-80.2, lookback_hours=72)
    signals = provider.fetch_normalized_signals(lat=27.7, lon=-80.2, lookback_hours=72)

    assert weather["rainfall_24h_mm"] == 48
    assert weather["rainfall_48h_mm"] == 96
    assert weather["rainfall_72h_mm"] == 144
    assert weather["temperature_c"] == 24
    assert weather["wind_speed_kmh"] == 12
    assert any(signal["signal_type"] == "weather_rainfall" and signal["value"] == 144 for signal in signals)
    assert all(signal["source"]["provider"] == "open_meteo" for signal in signals)
    rainfall_signal = next(signal for signal in signals if signal["signal_type"] == "weather_rainfall")
    assert rainfall_signal["location"]["geo"]["coordinates"] == [-80.2, 27.7]
    assert rainfall_signal["visibility"] == "public"
    assert rainfall_signal["risk_relevance"]["factors"] == ["rainfall_runoff"]
    assert rainfall_signal["data_freshness"]["status"] == "fresh"
    assert rainfall_signal["provider_timestamp"]


def test_open_meteo_cache_avoids_repeated_provider_calls(monkeypatch):
    open_meteo._CACHE.clear()
    calls = {"count": 0}

    def fake_urlopen(_url, timeout=10):
        calls["count"] += 1
        return FakeResponse(hourly_payload(rain=1.0))

    monkeypatch.setattr(open_meteo, "urlopen", fake_urlopen)
    provider = OpenMeteoProvider()
    provider.fetch_recent_weather(lat=27.7, lon=-80.2, lookback_hours=72)
    cached = provider.fetch_recent_weather(lat=27.7, lon=-80.2, lookback_hours=72)

    assert calls["count"] == 1
    assert cached["cached"] is True


def test_open_meteo_stale_cache_expires(monkeypatch):
    open_meteo._CACHE.clear()
    calls = {"count": 0}

    def fake_urlopen(_url, timeout=10):
        calls["count"] += 1
        return FakeResponse(hourly_payload(rain=float(calls["count"])))

    monkeypatch.setattr(open_meteo, "urlopen", fake_urlopen)
    provider = OpenMeteoProvider(cache_seconds=10)
    first = provider.fetch_recent_weather(lat=27.7, lon=-80.2, lookback_hours=72)
    key = (round(27.7, 4), round(-80.2, 4), 72)
    cached_at, cached_payload = open_meteo._CACHE[key]
    open_meteo._CACHE[key] = (cached_at - timedelta(seconds=11), cached_payload)
    second = provider.fetch_recent_weather(lat=27.7, lon=-80.2, lookback_hours=72)

    assert calls["count"] == 2
    assert first["rainfall_72h_mm"] == 72
    assert second["rainfall_72h_mm"] == 144
    assert second["cached"] is False


def test_warning_endpoint_uses_live_open_meteo_and_records_health(monkeypatch):
    client, db = make_client()
    timestamp = datetime.now(timezone.utc)

    def fake_signals(**_kwargs):
        return [
            {
                "signal_type": "weather_rainfall",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=12),
                "confidence": 0.85,
                "source": {"provider": "open_meteo", "dataset": "test"},
                "risk_relevance": {"score": 0.8, "factors": ["rainfall_runoff"]},
                "visibility": "public",
                "value": 120,
                "units": "mm",
                "location": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
            }
        ]

    monkeypatch.setattr("app.api_v1.fetch_live_open_meteo_signals", fake_signals)
    response = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&use_open_meteo=true&bypass_cache=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["warning_score"] > 0
    assert payload["data_freshness"]["open_meteo"]["status"] == "fresh"
    assert db[COLLECTIONS["provider_runs"]].docs
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "healthy"
    assert db[COLLECTIONS["provider_health"]].docs[0]["last_success"]
    assert db[COLLECTIONS["provider_health"]].docs[0]["last_error"] is None


def test_open_meteo_failure_does_not_crash_warning_endpoint(monkeypatch):
    client, db = make_client()

    def fail(**_kwargs):
        raise RuntimeError("provider timeout")

    monkeypatch.setattr("app.api_v1.fetch_live_open_meteo_signals", fail)
    response = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&use_open_meteo=true&bypass_cache=true")

    assert response.status_code == 200
    payload = response.json()
    assert "open_meteo" in payload["missing_data_sources"]
    assert payload["confidence"] < 0.9
    assert db[COLLECTIONS["provider_failures"]].docs
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "degraded"
    assert db[COLLECTIONS["provider_health"]].docs[0]["last_error"]
    assert "provider timeout" not in str(payload)


def test_alert_evaluation_can_use_live_rainfall_for_decision(monkeypatch):
    client, _db = make_client()
    timestamp = datetime.now(timezone.utc)

    def fake_signals(**_kwargs):
        return [
            {
                "signal_type": "weather_rainfall",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=12),
                "confidence": 0.85,
                "source": {"provider": "open_meteo", "dataset": "test"},
                "risk_relevance": {"score": 0.8, "factors": ["rainfall_runoff"]},
                "visibility": "public",
                "value": 120,
                "units": "mm",
                "location": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
            }
        ]

    monkeypatch.setattr("app.api_v1.fetch_live_open_meteo_signals", fake_signals)
    response = client.post(
        "/api/v1/alerts/evaluate?use_open_meteo=true",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 69, "quiet_day_delta": 20, "confidence": 0.7},
    )

    assert response.status_code == 200
    assert any(alert["alert_type"] == "general_warning" for alert in response.json()["alerts"])


def test_open_meteo_failure_does_not_crash_alert_evaluation(monkeypatch):
    client, db = make_client()

    def fail(**_kwargs):
        raise RuntimeError("stack trace should not leak")

    monkeypatch.setattr("app.api_v1.fetch_live_open_meteo_signals", fail)
    response = client.post(
        "/api/v1/alerts/evaluate?use_open_meteo=true",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 80, "quiet_day_delta": 20, "confidence": 0.7},
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(alert["alert_type"] == "general_warning" for alert in payload["alerts"])
    assert "stack trace should not leak" not in str(payload)
    assert db[COLLECTIONS["provider_failures"]].docs
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "degraded"


def test_use_open_meteo_false_bypasses_provider_fetch(monkeypatch):
    client, _db = make_client()

    def fail_if_called(**_kwargs):
        raise AssertionError("Open-Meteo should not be called")

    monkeypatch.setattr("app.api_v1.fetch_live_open_meteo_signals", fail_if_called)
    warning = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&bypass_cache=true")
    alert = client.post(
        "/api/v1/alerts/evaluate",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 80, "quiet_day_delta": 20},
    )

    assert warning.status_code == 200
    assert alert.status_code == 200
