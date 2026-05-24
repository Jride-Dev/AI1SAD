from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "hawaii_sharktober_quiet": ReplayScenario(
        scenario_id="hawaii_sharktober_quiet",
        label="Hawaii October quiet conditions",
        lat=21.3,
        lon=-157.8,
        timestamp=datetime(2025, 10, 5, 10, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=5.0,
        river_mouth_distance_km=10.0,
        sea_surface_temp_c=26.0,
        sst_anomaly_c=0.2,
        vessel_activity_index=0.1,
        human_exposure_index=0.4,
        month=10,
        activity_context="surfing",
        radius_km=25.0,
        expected_warning_band="low",
        tags=["hawaii", "october", "quiet"],
    )
}
