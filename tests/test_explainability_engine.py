from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import get_database
from app.services.alert_engine import evaluate_alerts
from app.services.explainability_engine import build_explanation
from tests.test_public_api_privacy import FakeDB


def make_client(db: FakeDB | None = None) -> tuple[TestClient, FakeDB]:
    fake_db = db or FakeDB()
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_database] = lambda: fake_db
    return TestClient(test_app), fake_db


def test_explanation_includes_factor_contributions():
    payload = {
        "location": {"geo": {"type": "Point", "coordinates": [115.515, -31.983]}},
        "warning_score": 12,
        "surveillance_priority_score": 82,
        "activity_context_score": 58,
        "dominant_factors": [
            {"factor": "activity_hazard_score", "points": 20, "rationale": "Activity drives operational review."},
            {"factor": "reef_dropoff_habitat_proximity", "points": 13, "rationale": "Reef habitat context."},
        ],
        "data_sources_used": ["reef_features"],
        "missing_data_sources": ["weather_observations"],
    }
    explanation = build_explanation(payload, output_type="surveillance")
    assert explanation["factor_contributions"]
    assert explanation["factor_contributions"][0]["factor"] == "activity_hazard_score"
    assert explanation["disclaimer"]


def test_explanation_includes_confidence_breakdown_and_freshness():
    explanation = build_explanation(
        {
            "warning_score": 18,
            "dominant_factors": [],
            "data_sources_used": ["weather_observations"],
            "missing_data_sources": ["ocean_observations"],
            "data_freshness": {"open_meteo": {"status": "present"}},
        },
        output_type="location",
    )
    assert "overall_confidence" in explanation["confidence_breakdown"]
    assert explanation["data_freshness"]["open_meteo"]["status"] == "present"
    assert explanation["missing_signal_impact"][0]["source"] == "ocean_observations"


def test_high_surveillance_low_warning_interpretation():
    explanation = build_explanation(
        {
            "warning_score": 10,
            "surveillance_priority_score": 88,
            "activity_context_score": 55,
            "dominant_factors": [{"factor": "reef_dropoff_habitat_proximity", "points": 18}],
        },
        output_type="surveillance",
    )
    assert "low general environmental warning" in explanation["operational_interpretation"].lower()
    assert explanation["recommended_surveillance_pattern"] == "reef_edge_expanding_grid"


def test_replay_explanation_endpoint_includes_version_metadata():
    client, _db = make_client()
    response = client.get("/api/v1/explain/replay?scenario_id=queensland_spearfishing_reef_tiger_bull_2026")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["model_version"]
    assert payload["metadata"]["replay_asset_version"]
    assert payload["factor_contributions"]


def test_alert_explanation_includes_recommended_action():
    alerts = evaluate_alerts(
        {
            "lat": -31.9826564,
            "lon": 115.5153234,
            "warning_score": 0,
            "activity_hazard_score": 58,
            "surveillance_priority_score": 99,
            "confidence": 0.5,
            "dominant_factors": [{"factor": "reef_dropoff_habitat_proximity", "points": 18}],
        }
    )
    explanation = build_explanation(alerts[0], output_type="alert")
    assert explanation["recommended_action"]
    assert "predict" in explanation["disclaimer"].lower()


def test_location_explanation_endpoint_returns_missing_source_info():
    client, _db = make_client()
    response = client.get(
        "/api/v1/explain/location?lat=-31.9826564&lon=115.5153234&activity_context=spearfishing&suspected_species=white%20shark"
    )
    assert response.status_code == 200
    payload = response.json()
    assert "missing_data_sources" in payload
    assert "confidence_breakdown" in payload
    assert "recommended_action" in payload
