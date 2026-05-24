from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "south_africa_white_shark_surf_seal_colony": ReplayScenario(
        scenario_id="south_africa_white_shark_surf_seal_colony",
        label="South Africa white shark surf near seal colony context",
        lat=-34.1,
        lon=18.5,
        timestamp=datetime(2025, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=0.0,
        river_mouth_distance_km=12.0,
        sea_surface_temp_c=18.5,
        sst_anomaly_c=0.3,
        vessel_activity_index=0.2,
        human_exposure_index=0.6,
        biological_events=[
            {"event_type": "seal colony prey activity", "observed_at": "2025-12-20T06:00:00Z", "visibility": "public"}
        ],
        month=12,
        activity_context="surfing",
        suspected_species="white shark",
        radius_km=15.0,
        expected_surveillance_band="moderate",
        tags=["south_africa", "white_shark", "seal_colony", "surf"],
    )
}
