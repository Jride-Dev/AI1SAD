from __future__ import annotations

from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class ConfidenceDecomposition:
    SOURCE_WEIGHTS: dict[str, float] = {
        "weather_observations": 0.15,
        "ocean_observations": 0.15,
        "vessel_activity": 0.10,
        "biological_events": 0.15,
        "human_exposure_estimates": 0.10,
        "recent_interactions": 0.15,
        "sighting_reports": 0.10,
        "reef_features": 0.05,
        "regional_risk_profiles": 0.05,
    }

    def decompose(self, *, data_sources_used: list[str], missing_data_sources: list[str], stale_sources: list[str] | None = None) -> dict[str, Any]:
        stale_sources = stale_sources or []
        present = set(data_sources_used)
        missing = set(missing_data_sources)
        stale = set(stale_sources)
        all_expected = set(self.SOURCE_WEIGHTS.keys())

        if not all_expected:
            return self._result(0.5, {})

        coverage_score = len(present & all_expected) / len(all_expected)
        freshness_penalty = len(stale & all_expected) * 0.08
        missing_penalty = len(missing & all_expected) * 0.06

        source_breakdown: dict[str, dict[str, Any]] = {}
        for source, weight in self.SOURCE_WEIGHTS.items():
            status = "present" if source in present else ("stale" if source in stale else "missing")
            source_breakdown[source] = {
                "weight": weight,
                "status": status,
                "contribution": round(weight, 4),
            }

        coverage_confidence = clamp(coverage_score)
        freshness_confidence = clamp(1.0 - freshness_penalty)
        completeness_confidence = clamp(1.0 - missing_penalty)
        overall = clamp(coverage_confidence * 0.4 + freshness_confidence * 0.3 + completeness_confidence * 0.3)

        return self._result(overall, {
            "coverage_confidence": round(coverage_confidence, 4),
            "freshness_confidence": round(freshness_confidence, 4),
            "completeness_confidence": round(completeness_confidence, 4),
            "coverage_score": round(coverage_score, 4),
            "freshness_penalty": round(freshness_penalty, 4),
            "missing_penalty": round(missing_penalty, 4),
            "source_details": source_breakdown,
        })

    def _result(self, overall: float, components: dict[str, Any]) -> dict[str, Any]:
        return {
            "overall_confidence": round(overall, 4),
            "confidence_band": self._band(overall),
            "components": components,
        }

    @staticmethod
    def _band(value: float) -> str:
        if value >= 0.85:
            return "high"
        if value >= 0.65:
            return "moderate"
        if value >= 0.45:
            return "low"
        return "very_low"
