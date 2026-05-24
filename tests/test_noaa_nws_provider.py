from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import COLLECTIONS, get_database
from app.providers import noaa_nws
from app.providers.noaa_nws import NoaaNwsProvider, classify_event
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


def nws_payload(events: list[str]) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "features": [
            {
                "id": f"alert-{index}",
                "properties": {
                    "id": f"alert-{index}",
                    "event": event,
                    "headline": f"{event} headline",
                    "severity": "Moderate",
                    "certainty": "Likely",
                    "urgency": "Expected",
                    "effective": now.isoformat().replace("+00:00", "Z"),
                    "expires": (now + timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
                },
            }
            for index, event in enumerate(events)
        ]
    }


def make_client(db: FakeDB | None = None) -> tuple[TestClient, FakeDB]:
    fake_db = db or FakeDB()
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_database] = lambda: fake_db
    return TestClient(test_app), fake_db


def test_noaa_nws_classifies_supported_alert_types():
    assert classify_event("Flood Warning")[0] == "flood_alert"
    assert classify_event("Severe Thunderstorm Warning")[0] == "thunderstorm_alert"
    assert classify_event("Rip Current Statement")[0] == "rip_current_alert"
    assert classify_event("Coastal Flood Advisory")[0] == "coastal_flood_alert"
    assert classify_event("High Surf Advisory")[0] == "high_surf_alert"
    assert classify_event("Marine Weather Statement")[0] == "marine_warning"


def test_noaa_nws_fetches_and_normalizes_alert_signals(monkeypatch):
    noaa_nws._CACHE.clear()

    def fake_urlopen(_request, timeout=10):
        return FakeResponse(nws_payload(["Flood Warning", "Rip Current Statement"]))

    monkeypatch.setattr(noaa_nws, "urlopen", fake_urlopen)
    provider = NoaaNwsProvider()
    signals = provider.fetch_normalized_signals(lat=27.7, lon=-80.2)

    types = {signal["signal_type"] for signal in signals}
    assert {"flood_alert", "rip_current_alert"} <= types
    assert all(signal["source"]["provider"] == "noaa_nws" for signal in signals)
    assert all(signal["source"]["dataset"] == "nws_active_alerts" for signal in signals)
    assert all(signal["visibility"] == "public" for signal in signals)
    assert all(signal["data_freshness"]["status"] == "fresh" for signal in signals)
    assert all(signal["provider_timestamp"] for signal in signals)
    assert all(signal["expires_at"] for signal in signals)
    assert all(signal["severity"] == "Moderate" for signal in signals)
    assert all(signal["alert_event"] for signal in signals)


def test_noaa_nws_cache_and_stale_expiry(monkeypatch):
    noaa_nws._CACHE.clear()
    calls = {"count": 0}

    def fake_urlopen(_request, timeout=10):
        calls["count"] += 1
        event = "Flood Warning" if calls["count"] == 1 else "High Surf Advisory"
        return FakeResponse(nws_payload([event]))

    monkeypatch.setattr(noaa_nws, "urlopen", fake_urlopen)
    provider = NoaaNwsProvider(cache_seconds=10)
    first = provider.fetch_active_alerts(lat=27.7, lon=-80.2)
    cached = provider.fetch_active_alerts(lat=27.7, lon=-80.2)
    key = (round(27.7, 4), round(-80.2, 4))
    cached_at, cached_payload = noaa_nws._CACHE[key]
    noaa_nws._CACHE[key] = (cached_at - timedelta(seconds=11), cached_payload)
    refreshed = provider.fetch_active_alerts(lat=27.7, lon=-80.2)

    assert calls["count"] == 2
    assert cached["cached"] is True
    assert first["alerts"][0]["signal_type"] == "flood_alert"
    assert refreshed["alerts"][0]["signal_type"] == "high_surf_alert"


def test_noaa_nws_outside_us_returns_not_applicable_without_fetch(monkeypatch):
    noaa_nws._CACHE.clear()

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("NOAA/NWS should not be called outside supported U.S. coordinates")

    monkeypatch.setattr(noaa_nws, "urlopen", fail_if_called)
    provider = NoaaNwsProvider()
    response = provider.fetch_active_alerts(lat=-31.9, lon=115.8)

    assert response["status"] == "not_applicable"
    assert response["alerts"] == []


def test_warning_endpoint_uses_noaa_nws_alerts_and_records_health(monkeypatch):
    client, db = make_client()
    timestamp = datetime.now(timezone.utc)

    def fake_signals(**_kwargs):
        return [
            {
                "signal_type": "flood_alert",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=4),
                "confidence": 0.75,
                "source": {"provider": "noaa_nws", "dataset": "test"},
                "risk_relevance": {"score": 0.8, "factors": ["flooding", "runoff"]},
                "visibility": "public",
                "value": 1,
                "units": "alert",
                "location": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
                "headline": "Flood Warning headline",
            }
        ]

    monkeypatch.setattr("app.api_v1.fetch_live_noaa_nws_signals", fake_signals)
    response = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&use_noaa_nws=true&bypass_cache=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["signals"]["weather_alert_score"] == 8
    assert payload["warning_score"] >= 8
    assert payload["data_freshness"]["noaa_nws"]["status"] == "fresh"
    assert db[COLLECTIONS["provider_runs"]].docs
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "healthy"


def test_noaa_nws_failure_does_not_crash_warning_or_alert(monkeypatch):
    client, db = make_client()

    def fail(**_kwargs):
        raise RuntimeError("sensitive stack trace text")

    monkeypatch.setattr("app.api_v1.fetch_live_noaa_nws_signals", fail)
    warning = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&use_noaa_nws=true&bypass_cache=true")
    alert = client.post(
        "/api/v1/alerts/evaluate?use_noaa_nws=true",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 80, "quiet_day_delta": 20, "confidence": 0.7},
    )

    assert warning.status_code == 200
    assert alert.status_code == 200
    assert "noaa_nws" in warning.json()["missing_data_sources"]
    assert "sensitive stack trace text" not in str(warning.json())
    assert "sensitive stack trace text" not in str(alert.json())
    assert db[COLLECTIONS["provider_failures"]].docs
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "degraded"


def test_noaa_nws_outside_us_warning_status_is_not_applicable(monkeypatch):
    client, db = make_client()

    def fail_if_called(**_kwargs):
        raise AssertionError("NOAA/NWS should not be called outside supported U.S. coordinates")

    monkeypatch.setattr("app.api_v1.fetch_live_noaa_nws_signals", fail_if_called)
    response = client.get("/api/v1/warnings/location?lat=-31.9&lon=115.8&use_noaa_nws=true&bypass_cache=true")
    baseline = client.get("/api/v1/warnings/location?lat=-31.9&lon=115.8&bypass_cache=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_freshness"]["noaa_nws"]["status"] == "not_applicable"
    assert "noaa_nws" not in payload["missing_data_sources"]
    assert payload["confidence"] == baseline.json()["confidence"]
    assert db[COLLECTIONS["provider_health"]].docs[0]["status"] == "not_applicable"


def test_generic_weather_alert_is_lower_weight_than_coastal_alerts():
    from app.services.signal_broker import warning_inputs_from_signals

    timestamp = datetime.now(timezone.utc)
    generic = warning_inputs_from_signals(
        [
            {
                "signal_type": "weather_alert",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=4),
                "confidence": 0.75,
                "source": {"provider": "noaa_nws", "dataset": "test"},
                "risk_relevance": {"score": 0.45, "factors": ["weather_alert"]},
                "visibility": "public",
                "value": 1,
            }
        ]
    )
    coastal = warning_inputs_from_signals(
        [
            {
                "signal_type": "coastal_flood_alert",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=4),
                "confidence": 0.75,
                "source": {"provider": "noaa_nws", "dataset": "test"},
                "risk_relevance": {"score": 0.75, "factors": ["coastal_flood"]},
                "visibility": "public",
                "value": 1,
            },
            {
                "signal_type": "rip_current_alert",
                "timestamp": timestamp,
                "expires_at": timestamp + timedelta(hours=4),
                "confidence": 0.75,
                "source": {"provider": "noaa_nws", "dataset": "test"},
                "risk_relevance": {"score": 0.75, "factors": ["rip_current"]},
                "visibility": "public",
                "value": 1,
            },
        ]
    )

    assert generic["weather_alert_score"] == 3
    assert coastal["weather_alert_score"] == 8


def test_use_noaa_nws_false_bypasses_provider_fetch(monkeypatch):
    client, _db = make_client()

    def fail_if_called(**_kwargs):
        raise AssertionError("NOAA/NWS should not be called")

    monkeypatch.setattr("app.api_v1.fetch_live_noaa_nws_signals", fail_if_called)
    warning = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&bypass_cache=true")
    alert = client.post(
        "/api/v1/alerts/evaluate",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 80, "quiet_day_delta": 20},
    )

    assert warning.status_code == 200
    assert alert.status_code == 200
