from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.explainability_engine import model_metadata
from app.services.warning_engine import WARNING_DISCLAIMER


def _metadata() -> dict[str, str]:
    return model_metadata(replay=True)


def _item(
    *,
    replay_id: str,
    title: str,
    region: str,
    coordinates: dict[str, float],
    observed_at: str | None,
    activity_context: str,
    species_context: str,
    replay_output: dict[str, Any],
    quiet_day_comparison: dict[str, Any],
    factor_summary: list[dict[str, Any]],
    explanation_summary: str,
    heatmap_asset: str | None,
) -> dict[str, Any]:
    metadata = _metadata()
    return {
        "id": replay_id,
        "title": title,
        "region": region,
        "coordinates": coordinates,
        "observed_at": observed_at,
        "activity_context": activity_context,
        "species_context": species_context,
        "replay_output": replay_output,
        "quiet_day_comparison": quiet_day_comparison,
        "factor_summary": factor_summary,
        "explanation_summary": explanation_summary,
        "heatmap_asset": heatmap_asset,
        "model_version": metadata["model_version"],
        "scoring_revision": metadata["scoring_revision"],
        "provider_stack_version": metadata["provider_stack_version"],
        "generated_at": metadata["generated_at"],
        "disclaimer": WARNING_DISCLAIMER,
    }


REPLAY_LIBRARY: dict[str, dict[str, Any]] = {
    "horseshoe_reef_2026": _item(
        replay_id="horseshoe_reef_2026",
        title="Horseshoe Reef 2026",
        region="Western Australia",
        coordinates={"lat": -31.9827, "lon": 115.5153},
        observed_at="2026-05-16T00:00:00Z",
        activity_context="spearfishing",
        species_context="white shark regional suitability",
        replay_output={
            "warning_score": 18,
            "warning_band": "low",
            "activity_hazard_score": 58,
            "activity_hazard_band": "elevated",
            "surveillance_priority_score": 82,
            "surveillance_priority_band": "high",
            "confidence": 0.68,
        },
        quiet_day_comparison={
            "warning_score": 8,
            "activity_hazard_score": 4,
            "surveillance_priority_score": 26,
            "confidence": 0.72,
            "summary": "Quiet-day baseline remains low; surveillance priority rises when activity, reef habitat, and regional context are present.",
        },
        factor_summary=[
            {"factor": "activity_hazard_score", "points": 20.3},
            {"factor": "wa_white_shark_reef_spearfishing_context", "points": 18},
            {"factor": "reef_dropoff_habitat_proximity", "points": 13},
        ],
        explanation_summary="Low general warning with high operational surveillance priority for reef-edge review.",
        heatmap_asset="docs/assets/horseshoe_reef_2026_model_replay.svg",
    ),
    "queensland_spearfishing_reef_tiger_bull_2026": _item(
        replay_id="queensland_spearfishing_reef_tiger_bull_2026",
        title="Queensland Spearfishing 2026",
        region="Far North Queensland, Australia",
        coordinates={"lat": -18.0822, "lon": 146.4483},
        observed_at="2026-05-24T08:00:00Z",
        activity_context="spearfishing",
        species_context="tiger shark and bull shark operational context",
        replay_output={
            "warning_score": 22,
            "warning_band": "low",
            "activity_hazard_score": 64,
            "activity_hazard_band": "elevated",
            "surveillance_priority_score": 78,
            "surveillance_priority_band": "high",
            "confidence": 0.66,
        },
        quiet_day_comparison={
            "warning_score": 10,
            "activity_hazard_score": 8,
            "surveillance_priority_score": 31,
            "confidence": 0.7,
            "summary": "Quiet-day comparison stays lower without spearfishing, reef/dropoff, and tropical species context.",
        },
        factor_summary=[
            {"factor": "activity_hazard_score", "points": 22},
            {"factor": "reef_dropoff_habitat_proximity", "points": 13},
            {"factor": "regional_species_suitability", "points": 12},
        ],
        explanation_summary="Tropical reef spearfishing context increases operator review priority while public warning language remains bounded.",
        heatmap_asset="docs/assets/case_studies/queensland_spearfishing_2026_heatmap.svg",
    ),
    "florida_crowded_inlet_demo": _item(
        replay_id="florida_crowded_inlet_demo",
        title="Florida Crowded Inlet Demo",
        region="Florida",
        coordinates={"lat": 29.0258, "lon": -80.926},
        observed_at=None,
        activity_context="swimming/surfing/fishing",
        species_context="blacktip and bull shark regional context",
        replay_output={
            "warning_score": 46,
            "warning_band": "moderate",
            "activity_hazard_score": 48,
            "activity_hazard_band": "moderate",
            "surveillance_priority_score": 55,
            "surveillance_priority_band": "moderate",
            "confidence": 0.62,
        },
        quiet_day_comparison={
            "warning_score": 18,
            "activity_hazard_score": 14,
            "surveillance_priority_score": 24,
            "confidence": 0.68,
            "summary": "Crowding, inlet exposure, and mixed water activity raise review context above a quiet-day baseline.",
        },
        factor_summary=[
            {"factor": "human_exposure_index", "points": 14},
            {"factor": "inlet_runoff_context", "points": 12},
            {"factor": "activity_context", "points": 10},
        ],
        explanation_summary="Demo scenario for crowded inlet operations and environmental monitoring.",
        heatmap_asset=None,
    ),
    "hawaii_october_tiger_context_demo": _item(
        replay_id="hawaii_october_tiger_context_demo",
        title="Hawaii October Tiger Shark Context Demo",
        region="Hawaii",
        coordinates={"lat": 21.276, "lon": -157.824},
        observed_at=None,
        activity_context="general water activity",
        species_context="tiger shark seasonal context",
        replay_output={
            "warning_score": 28,
            "warning_band": "low",
            "activity_hazard_score": 24,
            "activity_hazard_band": "low",
            "surveillance_priority_score": 38,
            "surveillance_priority_band": "moderate",
            "confidence": 0.6,
        },
        quiet_day_comparison={
            "warning_score": 16,
            "activity_hazard_score": 12,
            "surveillance_priority_score": 22,
            "confidence": 0.66,
            "summary": "Seasonal context raises operator awareness modestly without changing the bounded public warning posture.",
        },
        factor_summary=[
            {"factor": "seasonal_species_context", "points": 10},
            {"factor": "regional_profile", "points": 8},
            {"factor": "human_exposure_index", "points": 6},
        ],
        explanation_summary="Demo scenario for October regional context and calm monitoring workflows.",
        heatmap_asset=None,
    ),
    "red_sea_anomaly_demo": _item(
        replay_id="red_sea_anomaly_demo",
        title="Red Sea Anomaly Demo",
        region="Red Sea",
        coordinates={"lat": 27.2579, "lon": 33.8116},
        observed_at=None,
        activity_context="diving/tourism corridor",
        species_context="oceanic whitetip anomaly context",
        replay_output={
            "warning_score": 52,
            "warning_band": "moderate",
            "activity_hazard_score": 36,
            "activity_hazard_band": "moderate",
            "surveillance_priority_score": 66,
            "surveillance_priority_band": "elevated",
            "confidence": 0.58,
        },
        quiet_day_comparison={
            "warning_score": 14,
            "activity_hazard_score": 9,
            "surveillance_priority_score": 20,
            "confidence": 0.64,
            "summary": "Anomaly context and tourism corridor exposure create a stronger operator-review case than a quiet baseline.",
        },
        factor_summary=[
            {"factor": "biological_event_context", "points": 18},
            {"factor": "vessel_tourism_corridor", "points": 12},
            {"factor": "regional_species_suitability", "points": 10},
        ],
        explanation_summary="Demo scenario for anomaly review, advisory context, and surveillance planning.",
        heatmap_asset=None,
    ),
}


def list_replay_library() -> list[dict[str, Any]]:
    return [deepcopy(item) for item in REPLAY_LIBRARY.values()]


def get_replay_library_item(replay_id: str) -> dict[str, Any] | None:
    item = REPLAY_LIBRARY.get(replay_id)
    return deepcopy(item) if item else None
