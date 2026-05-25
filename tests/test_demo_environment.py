from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.config import get_settings
from app.main import app as main_app
from app.mongodb import get_database
from tests.test_public_api_privacy import FakeDB


def make_api_client(db: FakeDB | None = None) -> tuple[TestClient, FakeDB]:
    fake_db = db or FakeDB()
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_database] = lambda: fake_db
    return TestClient(test_app), fake_db


def test_health_works_without_minimal_environment(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "")
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    client = TestClient(main_app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "demo"
    assert payload["database_configured"] is False
    get_settings.cache_clear()


def test_demo_status_endpoint(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("MONGODB_URI", "")
    get_settings.cache_clear()
    client, _db = make_api_client()
    response = client.get("/api/v1/demo/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_mode"] is True
    assert payload["admin_writes_enabled"] is False
    assert payload["private_internal_data_exposed"] is False
    get_settings.cache_clear()


def test_demo_scenarios_endpoint_is_public_safe(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    client, _db = make_api_client()
    response = client.get("/api/v1/demo/scenarios")
    assert response.status_code == 200
    payload = response.json()
    scenario_ids = {scenario["scenario_id"] for scenario in payload["scenarios"]}
    assert "horseshoe_reef_2026" in scenario_ids
    assert "queensland_spearfishing_reef_tiger_bull_2026" in scenario_ids
    assert "florida_crowded_beach_inlet" in scenario_ids
    assert "hawaii_october_tiger_context" in scenario_ids
    assert "red_sea_anomaly_context" in scenario_ids
    assert "private_notes" not in str(payload)
    assert "internal_rules" not in str(payload)
    get_settings.cache_clear()


def test_demo_mode_labels_public_responses(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    client, _db = make_api_client()
    response = client.get("/api/v1/replay/run?scenario_id=wa_spearfishing_reef_white")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"]["demo_mode"] is True
    assert payload["demo"]["demo_label"] == "AI1SAD controlled public demo"
    get_settings.cache_clear()


def test_admin_writes_disabled_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("ADMIN_EVENTS_ENABLED", "true")
    monkeypatch.setenv("ADMIN_SURVEILLANCE_ENABLED", "true")
    monkeypatch.setenv("ADMIN_ALERTS_ENABLED", "true")
    get_settings.cache_clear()
    client, _db = make_api_client()
    manual = client.post("/api/v1/admin/events/manual", json={"event_type": "baitfish_presence", "lat": 25, "lon": -80})
    interaction = client.post("/api/v1/admin/surveillance/interaction", json={"lat": 25, "lon": -80})
    alert = client.post("/api/v1/admin/alerts/acknowledge", json={"alert_id": "public-alert"})
    assert manual.status_code == 403
    assert interaction.status_code == 403
    assert alert.status_code == 403
    get_settings.cache_clear()
