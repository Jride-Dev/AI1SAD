from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.replay.scenarios import ReplayScenario
from app.replay.quiet_day import QuietDayBaseline
from app.replay.decay import apply_decay_to_signals
from app.replay.confidence import ConfidenceDecomposition
from app.replay.heatmap import HeatmapConfig, HeatmapGenerator
from app.risk_model import nearest_profile, REGIONAL_RISK_PROFILES
from app.services.warning_engine import calculate_warning
from app.services.surveillance_engine import score_surveillance_zones


@dataclass
class ReplayResult:
    scenario_id: str
    label: str
    timestamp: datetime
    location: dict[str, float]
    warning: dict[str, Any]
    surveillance: dict[str, Any] | None = None
    quiet_day_comparison: dict[str, Any] | None = None
    confidence_decomposition: dict[str, Any] | None = None
    error: str | None = None


class ReplayRunner:
    def __init__(self, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or REGIONAL_RISK_PROFILES
        self._quiet_day = QuietDayBaseline()
        self._confidence = ConfidenceDecomposition()

    def run_scenario(self, scenario: ReplayScenario) -> ReplayResult:
        try:
            now = scenario.timestamp
            profile = nearest_profile(scenario.lat, scenario.lon, self.profiles)
            profiles_list = self.profiles

            warning = calculate_warning(
                lat=scenario.lat,
                lon=scenario.lon,
                lookback_hours=scenario.lookback_hours,
                rainfall_72h_mm=scenario.rainfall_72h_mm,
                river_mouth_distance_km=scenario.river_mouth_distance_km,
                sea_surface_temp_c=scenario.sea_surface_temp_c,
                sst_anomaly_c=scenario.sst_anomaly_c,
                vessel_activity_index=scenario.vessel_activity_index,
                biological_events=scenario.biological_events,
                kelp_habitat_signals=scenario.kelp_habitat_signals,
                hawaii_habitat_signals=scenario.hawaii_habitat_signals,
                hawaii_tide_current_signals=scenario.hawaii_tide_current_signals,
                human_exposure_index=scenario.human_exposure_index,
                activity_context=scenario.activity_context,
                reef_habitat=scenario.reef_habitat,
                dropoff_habitat=scenario.dropoff_habitat,
                bait_activity=bool(scenario.biological_events),
                suspected_species=scenario.suspected_species,
                month=scenario.month,
                profiles=profiles_list,
            )

            reef_features = []
            if scenario.reef_habitat or scenario.dropoff_habitat:
                reef_features.append(
                    {
                        "visibility": "public",
                        "feature_type": "reef" if scenario.reef_habitat else "dropoff",
                        "name": scenario.reef_feature_name or "Replay reef/dropoff habitat context",
                        "location": {"geo": {"type": "Point", "coordinates": [scenario.lon, scenario.lat]}},
                    }
                )

            surveillance = score_surveillance_zones(
                lat=scenario.lat,
                lon=scenario.lon,
                radius_km=scenario.radius_km,
                mission_type="replay",
                lookback_hours=scenario.lookback_hours,
                activity_context=scenario.activity_context,
                suspected_species=scenario.suspected_species,
                river_mouth_distance_km=scenario.river_mouth_distance_km,
                month=scenario.month,
                profiles=profiles_list,
                recent_interactions=scenario.recent_interactions,
                sighting_reports=scenario.sighting_reports,
                reef_features=reef_features,
                as_of=scenario.timestamp,
                warning_inputs={
                    "rainfall_72h_mm": scenario.rainfall_72h_mm,
                    "sea_surface_temp_c": scenario.sea_surface_temp_c,
                    "sst_anomaly_c": scenario.sst_anomaly_c,
                    "vessel_activity_index": scenario.vessel_activity_index,
                    "biological_events": scenario.biological_events,
                    "kelp_habitat_signals": scenario.kelp_habitat_signals,
                    "hawaii_habitat_signals": scenario.hawaii_habitat_signals,
                    "hawaii_tide_current_signals": scenario.hawaii_tide_current_signals,
                    "human_exposure_index": scenario.human_exposure_index,
                },
            )

            quiet_day_comparison = self._quiet_day.compare(
                current=warning,
                baseline=self._quiet_day.baseline_warning(
                    lat=scenario.lat,
                    lon=scenario.lon,
                    month=scenario.month,
                    profiles=profiles_list,
                ),
            )

            confidence_components = self._confidence.decompose(
                data_sources_used=warning.get("data_sources_used", []),
                missing_data_sources=warning.get("missing_data_sources", []),
            )

            return ReplayResult(
                scenario_id=scenario.scenario_id,
                label=scenario.label,
                timestamp=now,
                location={"lat": scenario.lat, "lon": scenario.lon},
                warning=warning,
                surveillance=surveillance,
                quiet_day_comparison=quiet_day_comparison,
                confidence_decomposition=confidence_components,
            )
        except Exception as exc:
            return ReplayResult(
                scenario_id=scenario.scenario_id,
                label=scenario.label,
                timestamp=scenario.timestamp,
                location={"lat": scenario.lat, "lon": scenario.lon},
                warning={},
                error=str(exc),
            )

    def run_all(self, scenarios: dict[str, ReplayScenario] | None = None) -> dict[str, ReplayResult]:
        from app.replay.scenarios import REPLAY_SCENARIOS
        scenarios = scenarios or REPLAY_SCENARIOS
        results: dict[str, ReplayResult] = {}
        for scenario_id, scenario in scenarios.items():
            results[scenario_id] = self.run_scenario(scenario)
        return results

    def run_decay_analysis(self, scenario: ReplayScenario) -> dict[str, Any]:
        signals: list[dict[str, Any]] = []
        if scenario.biological_events:
            for event in scenario.biological_events:
                signals.append({
                    "signal_type": "biological_event",
                    "timestamp": event.get("observed_at", scenario.timestamp.isoformat()),
                    "value": 1.0,
                    "visibility": "public",
                })
        for signal in scenario.kelp_habitat_signals:
            signals.append({
                "signal_type": signal.get("signal_type", "kelp_forest_presence"),
                "timestamp": signal.get("observed_at", scenario.timestamp.isoformat()),
                "value": signal.get("value", 0.4),
                "visibility": "public",
            })
        for signal in scenario.hawaii_habitat_signals:
            signals.append(
                {
                    "signal_type": signal.get("signal_type", "reef_channel_habitat"),
                    "timestamp": signal.get("observed_at", scenario.timestamp.isoformat()),
                    "value": signal.get("value", 0.35),
                    "visibility": "public",
                }
            )
        for signal in scenario.hawaii_tide_current_signals:
            signals.append(
                {
                    "signal_type": signal.get("signal_type", "nearshore_current_context"),
                    "timestamp": signal.get("observed_at", scenario.timestamp.isoformat()),
                    "value": signal.get("value", 0.35),
                    "visibility": "public",
                }
            )
        if scenario.sea_surface_temp_c is not None:
            signals.append({
                "signal_type": "ocean_sst",
                "timestamp": scenario.timestamp.isoformat(),
                "value": scenario.sea_surface_temp_c,
                "visibility": "public",
            })
        if scenario.rainfall_72h_mm is not None:
            signals.append({
                "signal_type": "weather_rainfall",
                "timestamp": scenario.timestamp.isoformat(),
                "value": scenario.rainfall_72h_mm,
                "visibility": "public",
            })
        now = datetime.now(timezone.utc)
        decayed = apply_decay_to_signals(signals, now=now)
        return {
            "scenario_id": scenario.scenario_id,
            "replay_timestamp": scenario.timestamp.isoformat(),
            "current_time": now.isoformat(),
            "signal_count": len(signals),
            "decayed_signal_count": len(decayed),
            "signals": decayed,
        }

    def run_heatmap(
        self,
        lat: float,
        lon: float,
        radius_km: float = 25.0,
        grid_points: int = 20,
        activity_context: str | None = None,
        suspected_species: str | None = None,
        month: int | None = None,
    ) -> dict[str, Any]:
        config = HeatmapConfig(center_lat=lat, center_lon=lon, radius_km=radius_km, grid_points=grid_points)
        gen = HeatmapGenerator(config)
        return gen.generate_surveillance_grid(
            profiles=self.profiles,
            activity_context=activity_context,
            suspected_species=suspected_species,
            month=month,
        )
