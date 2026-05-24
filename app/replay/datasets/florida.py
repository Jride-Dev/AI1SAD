from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "florida_summer_heavy_rain": ReplayScenario(
        scenario_id="florida_summer_heavy_rain",
        label="Florida summer heavy rainfall near beach",
        lat=27.7,
        lon=-80.2,
        timestamp=datetime(2025, 7, 15, 14, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=85.0,
        river_mouth_distance_km=2.0,
        sea_surface_temp_c=28.5,
        sst_anomaly_c=1.2,
        vessel_activity_index=0.3,
        human_exposure_index=0.7,
        month=7,
        activity_context="swimming",
        radius_km=25.0,
        expected_warning_band="elevated",
        tags=["florida", "summer", "rainfall", "beach"],
    )
}
