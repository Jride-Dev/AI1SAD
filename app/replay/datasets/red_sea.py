from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "red_sea_oceanic_whitetip_feeding": ReplayScenario(
        scenario_id="red_sea_oceanic_whitetip_feeding",
        label="Red Sea oceanic whitetip feeding event signal",
        lat=20.5,
        lon=38.5,
        timestamp=datetime(2025, 7, 1, 6, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=0.0,
        river_mouth_distance_km=None,
        sea_surface_temp_c=30.0,
        sst_anomaly_c=0.5,
        vessel_activity_index=0.6,
        human_exposure_index=0.2,
        biological_events=[
            {"event_type": "whale carcass", "observed_at": "2025-07-01T04:00:00Z", "visibility": "public"}
        ],
        month=7,
        radius_km=50.0,
        expected_warning_band="elevated",
        tags=["red_sea", "oceanic_whitetip", "feeding_event"],
    )
}
