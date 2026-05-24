from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from app.replay.scenarios import REPLAY_SCENARIOS, ReplayScenario
from app.replay.runner import ReplayRunner
from app.replay.decay import SIGNAL_TYPE_DECAY_PARAMS, SignalDecayModel, apply_decay_to_signals
from app.replay.confidence import ConfidenceDecomposition
from app.replay.quiet_day import QuietDayBaseline
from app.replay.heatmap import HeatmapConfig, HeatmapGenerator


class TestReplayScenarios:
    def test_predefined_scenarios_exist(self):
        assert len(REPLAY_SCENARIOS) >= 5
        assert any("south_africa" in scenario.tags for scenario in REPLAY_SCENARIOS.values())

    def test_each_scenario_has_required_fields(self):
        for sid, scenario in REPLAY_SCENARIOS.items():
            assert scenario.scenario_id == sid
            assert scenario.label
            assert -90 <= scenario.lat <= 90
            assert -180 <= scenario.lon <= 180
            assert scenario.timestamp.tzinfo is not None

    def test_custom_scenario_construction(self):
        scenario = ReplayScenario(
            scenario_id="test_custom",
            label="Test scenario",
            lat=25.0,
            lon=-80.0,
            timestamp=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            rainfall_72h_mm=30.0,
            month=6,
            activity_context="surfing",
        )
        assert scenario.scenario_id == "test_custom"
        assert scenario.rainfall_72h_mm == 30.0
        assert scenario.month == 6


class TestReplayRunner:
    def test_run_florida_summer_scenario(self):
        scenario = REPLAY_SCENARIOS["florida_summer_heavy_rain"]
        runner = ReplayRunner()
        result = runner.run_scenario(scenario)
        assert result.error is None
        assert result.warning.get("warning_score", 0) > 0
        assert result.warning.get("warning_band") in {"low", "moderate", "elevated", "high"}
        assert result.quiet_day_comparison is not None
        assert result.confidence_decomposition is not None

    def test_run_hawaii_quiet_scenario(self):
        scenario = REPLAY_SCENARIOS["hawaii_sharktober_quiet"]
        runner = ReplayRunner()
        result = runner.run_scenario(scenario)
        assert result.error is None
        assert result.warning.get("warning_score", 0) >= 0

    def test_run_wa_spearfishing_scenario(self):
        scenario = REPLAY_SCENARIOS["wa_spearfishing_reef_white"]
        runner = ReplayRunner()
        result = runner.run_scenario(scenario)
        assert result.error is None
        surveillance_score = (result.surveillance or {}).get("zones", [{}])[0].get("surveillance_priority_score", 0)
        assert surveillance_score > 0

    def test_run_all_scenarios(self):
        runner = ReplayRunner()
        results = runner.run_all()
        assert len(results) == len(REPLAY_SCENARIOS)
        for sid, result in results.items():
            assert result.error is None, f"Scenario {sid} failed: {result.error}"

    def test_run_decay_analysis(self):
        scenario = REPLAY_SCENARIOS["red_sea_oceanic_whitetip_feeding"]
        runner = ReplayRunner()
        analysis = runner.run_decay_analysis(scenario)
        assert analysis["scenario_id"] == scenario.scenario_id
        assert analysis["signal_count"] > 0
        for signal in analysis["signals"]:
            assert "decay_weight" in signal
            assert "age_hours" in signal

    def test_heatmap_generation(self):
        runner = ReplayRunner()
        heatmap = runner.run_heatmap(lat=27.7, lon=-80.2, radius_km=10.0, grid_points=10)
        assert heatmap["config"]["grid_cells"] > 0
        assert len(heatmap["cells"]) > 0
        assert "statistics" in heatmap


class TestSignalDecay:
    def test_decay_weight_fresh_signal(self):
        model = SignalDecayModel(half_life_hours=24.0)
        assert model.decay_weight(0) == 1.0
        assert model.decay_weight(1) > 0.9

    def test_decay_weight_half_life(self):
        model = SignalDecayModel(half_life_hours=24.0)
        weight = model.decay_weight(24.0)
        assert abs(weight - 0.5) < 0.01

    def test_decay_weight_expired(self):
        model = SignalDecayModel(half_life_hours=24.0, expiry_multiplier=3.0)
        assert model.decay_weight(72.0) == 0.0
        assert model.decay_weight(100.0) == 0.0

    def test_effective_value(self):
        model = SignalDecayModel(half_life_hours=24.0)
        result = model.effective_value(100.0, 24.0)
        assert abs(result - 50.0) < 1.0

    def test_type_specific_params(self):
        assert "weather_rainfall" in SIGNAL_TYPE_DECAY_PARAMS
        assert "sighting" in SIGNAL_TYPE_DECAY_PARAMS
        assert "carcass" in SIGNAL_TYPE_DECAY_PARAMS
        assert "biological_event" in SIGNAL_TYPE_DECAY_PARAMS
        assert SIGNAL_TYPE_DECAY_PARAMS["weather_rainfall"]["half_life_hours"] == 6.0

    def test_apply_decay_to_signals_empty(self):
        result = apply_decay_to_signals([])
        assert result == []

    def test_apply_decay_to_signals(self):
        now = datetime.now(timezone.utc)
        signals = [
            {"signal_type": "weather_rainfall", "timestamp": now, "value": 50.0, "visibility": "public"},
            {"signal_type": "biological_event", "timestamp": now, "value": 1.0, "visibility": "public"},
        ]
        result = apply_decay_to_signals(signals, now=now)
        assert len(result) == 2
        for signal in result:
            assert signal["decay_weight"] == 1.0

    def test_sighting_and_carcass_decay(self):
        now = datetime.now(timezone.utc)
        signals = [
            {"signal_type": "sighting", "timestamp": now, "value": 1.0, "visibility": "public"},
            {"signal_type": "carcass", "timestamp": now, "value": 1.0, "visibility": "public"},
        ]
        result = apply_decay_to_signals(signals, now=now)
        assert len(result) == 2
        assert {signal["signal_type"] for signal in result} == {"sighting", "carcass"}


class TestConfidenceDecomposition:
    def test_decompose_all_present(self):
        dec = ConfidenceDecomposition()
        result = dec.decompose(
            data_sources_used=["weather_observations", "ocean_observations", "vessel_activity", "biological_events", "human_exposure_estimates", "recent_interactions", "sighting_reports", "reef_features", "regional_risk_profiles"],
            missing_data_sources=[],
        )
        assert result["overall_confidence"] >= 0.85
        assert result["confidence_band"] == "high"

    def test_decompose_all_missing(self):
        dec = ConfidenceDecomposition()
        result = dec.decompose(
            data_sources_used=[],
            missing_data_sources=["weather_observations", "ocean_observations", "vessel_activity", "biological_events", "human_exposure_estimates", "recent_interactions"],
        )
        assert result["overall_confidence"] < 0.5

    def test_decompose_partial(self):
        dec = ConfidenceDecomposition()
        result = dec.decompose(
            data_sources_used=["weather_observations", "ocean_observations"],
            missing_data_sources=["vessel_activity", "biological_events", "human_exposure_estimates"],
        )
        assert 0.3 < result["overall_confidence"] < 0.8

    def test_decompose_with_stale(self):
        dec = ConfidenceDecomposition()
        result = dec.decompose(
            data_sources_used=["weather_observations", "ocean_observations"],
            missing_data_sources=[],
            stale_sources=["weather_observations"],
        )
        assert result["components"]["freshness_confidence"] < 1.0


class TestQuietDayBaseline:
    def test_baseline_warning_returns_scores(self):
        baseline = QuietDayBaseline()
        result = baseline.baseline_warning(lat=27.7, lon=-80.2, month=7)
        assert "warning_score" in result
        assert "warning_band" in result

    def test_compare_elevated_vs_baseline(self):
        baseline = QuietDayBaseline()
        current = {"warning_score": 60, "warning_band": "elevated", "confidence": 0.8, "missing_data_sources": []}
        base = {"warning_score": 15, "warning_band": "low", "confidence": 0.7}
        comparison = baseline.compare(current, base)
        assert comparison["delta"] == 45
        assert comparison["band_change"] is True

    def test_compare_quiet_vs_baseline(self):
        baseline = QuietDayBaseline()
        current = {"warning_score": 10, "warning_band": "low", "confidence": 0.8, "missing_data_sources": []}
        base = {"warning_score": 8, "warning_band": "low", "confidence": 0.7}
        comparison = baseline.compare(current, base)
        assert comparison["delta"] == 2
        assert comparison["band_change"] is False
        assert "near quiet-day" in comparison["interpretation"].lower()

    def test_interpret_various_deltas(self):
        baseline = QuietDayBaseline()
        assert "elevated" in baseline._interpret(25, 0.7, [])
        assert "baseline" in baseline._interpret(2, 0.8, [])
        assert "Below" in baseline._interpret(-15, 0.7, [])


class TestHeatmapGenerator:
    def test_grid_coordinates_count(self):
        config = HeatmapConfig(center_lat=27.7, center_lon=-80.2, radius_km=10.0, grid_points=10)
        gen = HeatmapGenerator(config)
        scorer_calls: list[tuple[float, float]] = []

        def dummy_scorer(lat: float, lon: float) -> dict[str, Any]:
            scorer_calls.append((lat, lon))
            return {"surveillance_priority_score": 25.0, "surveillance_priority_band": "moderate"}

        result = gen.generate(dummy_scorer)
        assert result["config"]["grid_cells"] > 0
        assert result["config"]["grid_cells"] == len(scorer_calls)
        assert result["statistics"]["min_score"] == 25.0
        assert result["statistics"]["max_score"] == 25.0

    def test_heatmap_statistics_vary(self):
        config = HeatmapConfig(center_lat=27.7, center_lon=-80.2, radius_km=10.0, grid_points=10)
        gen = HeatmapGenerator(config)
        call_count: int = 0

        def varying_scorer(lat: float, lon: float) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"warning_score": float(call_count * 10), "warning_band": "elevated"}

        result = gen.generate(varying_scorer)
        assert result["statistics"]["min_score"] < result["statistics"]["max_score"]

    def test_heatmap_generate_warning_grid(self):
        config = HeatmapConfig(center_lat=27.7, center_lon=-80.2, radius_km=5.0, grid_points=5)
        gen = HeatmapGenerator(config)
        result = gen.generate_warning_grid()
        assert result["config"]["grid_cells"] > 0
        for cell in result["cells"]:
            assert 0 <= cell["surveillance_priority_score"] <= 100

    def test_heatmap_generate_surveillance_grid_cells(self):
        config = HeatmapConfig(center_lat=-31.95, center_lon=115.86, radius_km=5.0, grid_points=5)
        gen = HeatmapGenerator(config)
        result = gen.generate_surveillance_grid(activity_context="spearfishing", suspected_species="white shark", month=2)
        assert result["score_type"] == "surveillance_priority_score"
        assert result["config"]["grid_cells"] > 0
        for cell in result["cells"]:
            assert "surveillance_priority_score" in cell
            assert "warning_score" in cell
            assert "activity_hazard_score" in cell
