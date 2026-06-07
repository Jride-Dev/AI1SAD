from __future__ import annotations

from tests.test_demo_environment import make_api_client


def test_replay_library_list_works():
    client, _db = make_api_client()
    response = client.get("/api/v1/replay/library")
    assert response.status_code == 200
    payload = response.json()
    replay_ids = {item["id"] for item in payload["results"]}
    assert "horseshoe_reef_2026" in replay_ids
    assert "queensland_spearfishing_reef_tiger_bull_2026" in replay_ids
    assert "florida_crowded_inlet_demo" in replay_ids
    assert "hawaii_october_tiger_context_demo" in replay_ids
    assert "red_sea_anomaly_demo" in replay_ids
    assert "piedade_boa_viagem_recife_2026" in replay_ids
    assert "michaelmas_island_albany_wa_2026" in replay_ids
    assert "lovers_point_pacific_grove_whale_carcass_2026" in replay_ids


def test_replay_library_detail_works():
    client, _db = make_api_client()
    response = client.get("/api/v1/replay/library/horseshoe_reef_2026")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "horseshoe_reef_2026"
    assert payload["replay_output"]["surveillance_priority_score"] >= 0
    assert payload["quiet_day_comparison"]["warning_score"] >= 0
    assert payload["factor_summary"]


def test_unknown_replay_library_item_returns_404():
    client, _db = make_api_client()
    response = client.get("/api/v1/replay/library/unknown-replay")
    assert response.status_code == 404


def test_replay_library_entries_include_version_metadata():
    client, _db = make_api_client()
    response = client.get("/api/v1/replay/library")
    assert response.status_code == 200
    for item in response.json()["results"]:
        assert item["model_version"]
        assert item["scoring_revision"]
        assert item["provider_stack_version"]
        assert item["generated_at"]
