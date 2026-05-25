from __future__ import annotations

from datetime import datetime, timezone

from app.replay.scenarios import ReplayScenario


SCENARIOS = {
    "queensland_spearfishing_reef_tiger_bull_2026": ReplayScenario(
        scenario_id="queensland_spearfishing_reef_tiger_bull_2026",
        label="Queensland spearfishing on tropical reef with tiger/bull shark operational context",
        lat=-18.082164764,
        lon=146.448303222,
        timestamp=datetime(2026, 5, 24, 8, 0, 0, tzinfo=timezone.utc),
        rainfall_72h_mm=0.0,
        river_mouth_distance_km=30.0,
        sea_surface_temp_c=29.0,
        sst_anomaly_c=0.2,
        vessel_activity_index=0.35,
        human_exposure_index=0.28,
        biological_events=[
            {
                "event_type": "reef_prey_context",
                "observed_at": "2026-05-24T06:00:00+00:00",
                "visibility": "public",
                "confidence": 0.55,
                "value": 0.5,
                "notes": "Replay context only: tropical reef/prey habitat signal, not a live carcass or verified bait event.",
            }
        ],
        month=5,
        activity_context="spearfishing",
        suspected_species="tiger shark",
        radius_km=12.0,
        expected_warning_band="low",
        expected_surveillance_band="elevated",
        reef_habitat=True,
        dropoff_habitat=True,
        reef_feature_name="Kennedy Shoal reef habitat context",
        tags=[
            "queensland",
            "australia",
            "great_barrier_reef",
            "spearfishing",
            "reef",
            "tiger_shark",
            "bull_shark",
        ],
    )
}
