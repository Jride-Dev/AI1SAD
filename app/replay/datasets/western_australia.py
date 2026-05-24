from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "wa_spearfishing_reef_white": ReplayScenario(
        scenario_id="wa_spearfishing_reef_white",
        label="Western Australia spearfishing on reef with white shark suitability",
        lat=-31.95,
        lon=115.86,
        timestamp=datetime(2025, 2, 10, 8, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=0.0,
        river_mouth_distance_km=15.0,
        sea_surface_temp_c=22.0,
        sst_anomaly_c=0.0,
        vessel_activity_index=0.2,
        human_exposure_index=0.3,
        month=2,
        activity_context="spearfishing",
        suspected_species="white shark",
        radius_km=10.0,
        expected_surveillance_band="elevated",
        tags=["western_australia", "spearfishing", "reef", "white_shark"],
    )
}
