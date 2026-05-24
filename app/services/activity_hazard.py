from __future__ import annotations

from typing import Any

from app.risk_model import band_for_score


HIGH_RISK_ACTIVITY_POINTS = {
    "spearfishing": 24,
    "diving_with_catch": 22,
    "diving with catch": 22,
    "fishing": 16,
    "fishing_near_reef": 20,
    "fishing near reef": 20,
    "swimming_near_bait": 18,
    "swimming near bait": 18,
}


def activity_hazard_score(
    *,
    activity_context: str | None = None,
    reef_habitat: bool = False,
    dropoff_habitat: bool = False,
    bait_activity: bool = False,
    suspected_species: str | None = None,
    regional_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    activity = (activity_context or "").lower().strip()
    species = (suspected_species or "").lower().strip()
    region = (regional_profile or {}).get("region_key")
    dominant_species = {item.lower() for item in (regional_profile or {}).get("dominant_species", [])}
    factors: list[dict[str, Any]] = []

    def add(factor: str, value: Any, points: float, rationale: str) -> None:
        factors.append({"factor": factor, "value": value, "points": points, "rationale": rationale})

    base_points = HIGH_RISK_ACTIVITY_POINTS.get(activity, 0)
    if base_points:
        add(
            "activity_context_hazard",
            activity_context,
            base_points,
            "Human activity context can increase encounter hazard; this is not attack probability or an intent claim.",
        )

    if activity in {"spearfishing", "diving_with_catch", "diving with catch"} and (reef_habitat or dropoff_habitat):
        add("catch_near_reef_or_dropoff", True, 14, "Catch handling near reef/dropoff habitat can increase search and encounter-hazard context.")

    if activity in {"fishing", "fishing_near_reef", "fishing near reef"} and (reef_habitat or dropoff_habitat):
        add("fishing_near_reef_or_dropoff", True, 10, "Fishing near reef/dropoff habitat can add bait, scent, discards, or hooked-fish cues.")

    if activity in {"swimming_near_bait", "swimming near bait"} or bait_activity:
        add("bait_activity_near_swimmers", bait_activity or activity_context, 12, "Swimming near bait/prey activity increases activity-context hazard.")

    if region == "western_australia" and activity == "spearfishing" and (reef_habitat or dropoff_habitat):
        if "white" in species or "white shark" in dominant_species:
            add(
                "wa_white_shark_spearfishing_reef_context",
                suspected_species or "regional white shark suitability",
                20,
                "Western Australia profile strongly weights spearfishing on reef/dropoff habitat where white shark suitability is known or suspected.",
            )

    score = min(100, round(sum(item["points"] for item in factors), 2))
    for factor in factors:
        factor["contribution"] = round(factor["points"] / score, 4) if score else 0
    return {
        "activity_context_score": score,
        "activity_context_band": band_for_score(score),
        "factors": sorted(factors, key=lambda item: item["points"], reverse=True),
        "disclaimer": "Activity hazard is not attack probability. It estimates hazard introduced by what the human is doing in context.",
    }
