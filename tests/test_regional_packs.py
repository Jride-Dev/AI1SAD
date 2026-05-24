from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import COLLECTIONS, get_database
from tests.test_public_api_privacy import FakeDB


def make_client(db: FakeDB | None = None) -> tuple[TestClient, FakeDB]:
    fake_db = db or FakeDB()
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_database] = lambda: fake_db
    return TestClient(test_app), fake_db


def test_core_works_without_regional_pack():
    client, _db = make_client()
    response = client.get("/api/v1/warnings/location?lat=0&lon=0&bypass_cache=true")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_pack"] == "core"
    assert payload["pack_notice"] is None
    assert "pack_features_used" in payload


def test_florida_coordinates_detect_pack_availability():
    client, _db = make_client()
    response = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&bypass_cache=true")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_pack"] == "core"
    assert payload["available_pack"] == "florida"
    assert payload["pack_notice"]


def test_active_pack_appears_when_pack_enabled():
    client, _db = make_client()
    response = client.get("/api/v1/warnings/location?lat=27.7&lon=-80.2&bypass_cache=true&enabled_packs=florida")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_pack"] == "florida"
    assert payload["pack_notice"] is None
    assert "florida_inlet_rules" in payload["pack_features_used"]


def test_wa_hawaii_and_red_sea_coordinates_detect_seed_pack_availability():
    db = FakeDB()
    db.collections[COLLECTIONS["regional_packs"]].docs = []
    client, _db = make_client(db)
    cases = [
        (-31.9826564, 115.5153234, "western_australia"),
        (21.3, -157.8, "hawaii"),
        (20.5, 38.5, "red_sea"),
    ]
    for lat, lon, expected_pack in cases:
        response = client.get(f"/api/v1/surveillance/search-zones?lat={lat}&lon={lon}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["active_pack"] == "core"
        assert payload["available_pack"] == expected_pack
        assert payload["pack_notice"]


def test_replay_and_alert_responses_include_pack_fields():
    client, _db = make_client()
    replay = client.get("/api/v1/replay/run?scenario_id=wa_spearfishing_reef_white&enabled_packs=western_australia")
    alert = client.post(
        "/api/v1/alerts/evaluate?enabled_packs=florida",
        json={"lat": 27.7, "lon": -80.2, "warning_score": 0, "surveillance_priority_score": 80, "activity_hazard_score": 0},
    )
    assert replay.status_code == 200
    assert alert.status_code == 200
    assert replay.json()["active_pack"] == "western_australia"
    assert alert.json()["active_pack"] == "florida"


def test_pack_public_routes_exclude_private_internal_records():
    client, _db = make_client()
    packs = client.get("/api/v1/packs")
    species = client.get("/api/v1/packs/florida/species")
    signals = client.get("/api/v1/packs/florida/signals")
    replays = client.get("/api/v1/packs/florida/replays")
    entitlements = client.get("/api/v1/access/entitlements")

    for response in [packs, species, signals, replays, entitlements]:
        assert response.status_code == 200
        assert "private" not in str(response.json()).lower()
        assert "internal" not in str(response.json()).lower()

    assert "florida" in {item["pack_id"] for item in packs.json()["results"]}
    assert species.json()["dominant_species"] == ["bull shark", "blacktip shark"]
    assert "rainfall_runoff" in signals.json()["environmental_signals"]
    assert "florida_summer_heavy_rain" in replays.json()["replay_scenarios"]
