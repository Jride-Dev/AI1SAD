from __future__ import annotations

from typing import Any

from app.replay.confidence import ConfidenceDecomposition
from app.services.warning_engine import calculate_warning


QUIET_DAY_INPUTS: dict[str, Any] = {
    "rainfall_72h_mm": 0.0,
    "river_mouth_distance_km": 20.0,
    "sea_surface_temp_c": 22.0,
    "sst_anomaly_c": 0.0,
    "vessel_activity_index": 0.1,
    "biological_events": [],
    "human_exposure_index": 0.3,
    "lookback_hours": 72,
}


class QuietDayBaseline:
    def __init__(self) -> None:
        self._confidence = ConfidenceDecomposition()

    def baseline_warning(self, *, lat: float, lon: float, month: int | None = None, profiles: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return calculate_warning(
            lat=lat,
            lon=lon,
            lookback_hours=72,
            rainfall_72h_mm=QUIET_DAY_INPUTS["rainfall_72h_mm"],
            river_mouth_distance_km=QUIET_DAY_INPUTS["river_mouth_distance_km"],
            sea_surface_temp_c=QUIET_DAY_INPUTS["sea_surface_temp_c"],
            sst_anomaly_c=QUIET_DAY_INPUTS["sst_anomaly_c"],
            vessel_activity_index=QUIET_DAY_INPUTS["vessel_activity_index"],
            biological_events=list(QUIET_DAY_INPUTS["biological_events"]),
            human_exposure_index=QUIET_DAY_INPUTS["human_exposure_index"],
            month=month,
            profiles=profiles,
        )

    def compare(self, current: dict[str, Any], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
        baseline = baseline or {}
        current_score = current.get("warning_score", 0)
        baseline_score = baseline.get("warning_score", 0)
        delta = round(current_score - baseline_score, 2)
        return {
            "current_warning_score": current_score,
            "baseline_warning_score": baseline_score,
            "delta": delta,
            "delta_percent": round((delta / baseline_score * 100) if baseline_score else 0, 2),
            "current_band": current.get("warning_band", "unknown"),
            "baseline_band": baseline.get("warning_band", "unknown"),
            "band_change": delta > 15,
            "current_confidence": current.get("confidence", 0),
            "baseline_confidence": baseline.get("confidence", 0),
            "missing_data_sources": current.get("missing_data_sources", []),
            "interpretation": self._interpret(delta, current.get("confidence", 0), current.get("missing_data_sources", [])),
        }

    @staticmethod
    def _interpret(delta: float, confidence: float, missing: list[str]) -> str:
        if delta < -10:
            return "Below quiet-day baseline."
        if delta > 20 and confidence >= 0.6:
            return "Notably elevated above quiet-day baseline."
        if delta > 10:
            return "Moderately elevated above quiet-day baseline."
        if not missing and confidence >= 0.7 and abs(delta) <= 5:
            return "Conditions near quiet-day baseline."
        return "Near quiet-day baseline with limited data."
