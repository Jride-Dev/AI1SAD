from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ReplayScenario:
    scenario_id: str
    label: str
    lat: float
    lon: float
    timestamp: datetime
    rainfall_72h_mm: float | None = None
    river_mouth_distance_km: float | None = None
    sea_surface_temp_c: float | None = None
    sst_anomaly_c: float | None = None
    vessel_activity_index: float | None = None
    human_exposure_index: float | None = None
    biological_events: list[dict[str, Any]] = field(default_factory=list)
    sighting_reports: list[dict[str, Any]] = field(default_factory=list)
    recent_interactions: list[dict[str, Any]] = field(default_factory=list)
    kelp_habitat_signals: list[dict[str, Any]] = field(default_factory=list)
    hawaii_habitat_signals: list[dict[str, Any]] = field(default_factory=list)
    hawaii_tide_current_signals: list[dict[str, Any]] = field(default_factory=list)
    hawaii_water_clarity_signals: list[dict[str, Any]] = field(default_factory=list)
    month: int | None = None
    activity_context: str | None = None
    suspected_species: str | None = None
    lookback_hours: int = 72
    radius_km: float = 25.0
    expected_warning_band: str | None = None
    expected_surveillance_band: str | None = None
    reef_habitat: bool = False
    dropoff_habitat: bool = False
    reef_feature_name: str | None = None
    use_regional_profiles: bool = True
    tags: list[str] = field(default_factory=list)


def load_region_scenarios() -> dict[str, ReplayScenario]:
    from app.replay.datasets.florida import SCENARIOS as FLORIDA
    from app.replay.datasets.hawaii import SCENARIOS as HAWAII
    from app.replay.datasets.queensland import SCENARIOS as QUEENSLAND
    from app.replay.datasets.red_sea import SCENARIOS as RED_SEA
    from app.replay.datasets.south_africa import SCENARIOS as SOUTH_AFRICA
    from app.replay.datasets.western_australia import SCENARIOS as WESTERN_AUSTRALIA
    from app.replay.datasets.brazil import SCENARIOS as BRAZIL

    scenarios: dict[str, ReplayScenario] = {}
    for region_pack in [FLORIDA, WESTERN_AUSTRALIA, QUEENSLAND, HAWAII, SOUTH_AFRICA, RED_SEA, BRAZIL]:
        scenarios.update(region_pack)
    return scenarios


REPLAY_SCENARIOS: dict[str, ReplayScenario] = load_region_scenarios()
