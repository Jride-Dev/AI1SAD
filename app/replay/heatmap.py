from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class HeatmapConfig:
    center_lat: float
    center_lon: float
    radius_km: float = 25.0
    step_km: float = 5.0
    grid_points: int = 20


def _grid_coordinates(config: HeatmapConfig) -> list[tuple[float, float]]:
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * __import__("math").cos(__import__("math").radians(config.center_lat))
    half_span_deg = (config.radius_km / max(km_per_deg_lat, 1)) / 2
    points: list[tuple[float, float]] = []
    for i in range(config.grid_points):
        fraction = (i / max(config.grid_points - 1, 1)) * 2 - 1
        lat = config.center_lat + fraction * half_span_deg
        for j in range(config.grid_points):
            fraction2 = (j / max(config.grid_points - 1, 1)) * 2 - 1
            lon = config.center_lon + fraction2 * half_span_deg
            dlat = (lat - config.center_lat) * km_per_deg_lat
            dlon = (lon - config.center_lon) * km_per_deg_lon
            distance_km = (dlat**2 + dlon**2) ** 0.5
            if distance_km <= config.radius_km:
                points.append((round(lat, 4), round(lon, 4)))
    return points


class HeatmapGenerator:
    def __init__(self, config: HeatmapConfig) -> None:
        self.config = config

    def generate(self, scorer: Callable[[float, float], dict[str, Any]]) -> dict[str, Any]:
        coords = _grid_coordinates(self.config)
        cells: list[dict[str, Any]] = []
        values: list[float] = []
        for lat, lon in coords:
            result = scorer(lat, lon)
            score = result.get("surveillance_priority_score", result.get("warning_score", result.get("priority_score", 0)))
            cells.append({
                "lat": lat,
                "lon": lon,
                "surveillance_priority_score": score,
                "surveillance_priority_band": result.get("surveillance_priority_band", result.get("priority_band", "unknown")),
                "warning_score": result.get("warning_score"),
                "warning_band": result.get("warning_band"),
                "activity_hazard_score": result.get("activity_context_score"),
                "activity_hazard_band": result.get("activity_context_band"),
            })
            values.append(score)

        if values:
            min_score = min(values)
            max_score = max(values)
            avg_score = round(sum(values) / len(values), 2)
        else:
            min_score = max_score = avg_score = 0.0

        return {
            "config": {
                "center_lat": self.config.center_lat,
                "center_lon": self.config.center_lon,
                "radius_km": self.config.radius_km,
                "grid_cells": len(cells),
            },
            "cells": cells,
            "statistics": {
                "min_score": round(min_score, 2),
                "max_score": round(max_score, 2),
                "avg_score": avg_score,
                "median_score": round(sorted(values)[len(values) // 2], 2) if values else 0,
            },
        }

    def generate_warning_grid(self, profiles: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        from app.services.warning_engine import calculate_warning

        def scorer(lat: float, lon: float) -> dict[str, Any]:
            return calculate_warning(
                lat=lat,
                lon=lon,
                lookback_hours=72,
                month=None,
                profiles=profiles,
            )
        return self.generate(scorer)

    def generate_surveillance_grid(
        self,
        *,
        profiles: list[dict[str, Any]] | None = None,
        activity_context: str | None = None,
        suspected_species: str | None = None,
        month: int | None = None,
    ) -> dict[str, Any]:
        from app.services.surveillance_engine import score_surveillance_zones

        def scorer(lat: float, lon: float) -> dict[str, Any]:
            zone = score_surveillance_zones(
                lat=lat,
                lon=lon,
                radius_km=self.config.radius_km,
                mission_type="replay_heatmap",
                lookback_hours=72,
                activity_context=activity_context,
                suspected_species=suspected_species,
                month=month,
                profiles=profiles,
            )["zones"][0]
            return {
                "surveillance_priority_score": zone["surveillance_priority_score"],
                "surveillance_priority_band": zone["surveillance_priority_band"],
                "warning_score": zone["warning_score"],
                "warning_band": zone["warning_band"],
                "activity_context_score": zone["activity_context_score"],
                "activity_context_band": zone["activity_context_band"],
            }

        result = self.generate(scorer)
        result["score_type"] = "surveillance_priority_score"
        return result

    def generate_risk_grid(self, profiles: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        from app.risk_model import nearest_profile, score_risk

        def scorer(lat: float, lon: float) -> dict[str, Any]:
            profile = (nearest_profile(lat, lon, profiles) if profiles else nearest_profile(lat, lon)) if profiles is not None else nearest_profile(lat, lon)
            result = score_risk(regional_profile=profile)
            return {"warning_score": result["warning_score"], "warning_band": result["warning_band"]}
        return self.generate(scorer)
