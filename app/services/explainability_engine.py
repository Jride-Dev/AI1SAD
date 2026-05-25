from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.disclaimers import AI1SAD_API_DISCLAIMER
from app.replay.confidence import ConfidenceDecomposition


MODEL_VERSION = "0.11.0"
SCORING_REVISION = "phase-11-explainability"
PROVIDER_STACK_VERSION = "phase-9-static-live-adapters"
REPLAY_ASSET_VERSION = "2026.05"


RECOMMENDATION_PATTERNS = {
    "reef_edge_expanding_grid": {
        "label": "Reef-edge expanding grid",
        "recommended_action": "Prioritize reef edge, dropoff, and adjacent current lines with expanding drone passes.",
    },
    "inlet_surf_zone_scan": {
        "label": "Inlet surf-zone scan",
        "recommended_action": "Scan inlet outflow, surf zone, and adjacent sandbars with repeated parallel passes.",
    },
    "shoreline_parallel_sweep": {
        "label": "Shoreline parallel sweep",
        "recommended_action": "Run parallel shoreline sweeps and maintain lookout coverage where human exposure is highest.",
    },
    "post_sighting_focus_area": {
        "label": "Post-sighting focus area",
        "recommended_action": "Concentrate monitoring around the latest verified sighting while checking adjacent travel corridors.",
    },
    "carcass_event_buffer_zone": {
        "label": "Carcass event buffer zone",
        "recommended_action": "Create a temporary buffer around the biological event and coordinate with wildlife authorities.",
    },
    "low_priority_observation": {
        "label": "Low-priority observation",
        "recommended_action": "Maintain routine observation and defer intensive drone coverage unless new signals arrive.",
    },
}


def model_metadata(*, replay: bool = False) -> dict[str, Any]:
    metadata = {
        "model_version": MODEL_VERSION,
        "scoring_revision": SCORING_REVISION,
        "provider_stack_version": PROVIDER_STACK_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if replay:
        metadata["replay_asset_version"] = REPLAY_ASSET_VERSION
    return metadata


def _score(payload: dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in payload and payload[key] is not None:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _location(payload: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if payload.get("location"):
        return payload["location"]
    if payload.get("center"):
        return payload["center"]
    if payload.get("zone", {}).get("location"):
        return payload["zone"]["location"]
    if "lat" in payload and "lon" in payload:
        return {"geo": {"type": "Point", "coordinates": [payload["lon"], payload["lat"]]}}
    return fallback or {"geo": {"type": "Point", "coordinates": [0, 0]}}


def factor_contributions(factors: list[dict[str, Any]], total_score: float | None = None) -> list[dict[str, Any]]:
    total = total_score if total_score and total_score > 0 else sum(float(item.get("points", 0) or 0) for item in factors)
    breakdown = []
    for item in factors:
        points = float(item.get("points", 0) or 0)
        contribution = item.get("contribution")
        if contribution is None:
            contribution = round(points / total, 4) if total else 0
        breakdown.append(
            {
                "factor": item.get("factor"),
                "value": item.get("value"),
                "points": round(points, 4),
                "contribution": round(float(contribution or 0), 4),
                "rationale": item.get("rationale", ""),
            }
        )
    return sorted(breakdown, key=lambda item: item["points"], reverse=True)


def confidence_breakdown(payload: dict[str, Any]) -> dict[str, Any]:
    existing = payload.get("confidence_breakdown") or payload.get("confidence_decomposition")
    if isinstance(existing, dict) and "overall_confidence" in existing:
        return existing
    return ConfidenceDecomposition().decompose(
        data_sources_used=list(payload.get("data_sources_used", [])),
        missing_data_sources=list(payload.get("missing_data_sources", [])),
        stale_sources=[source for source, info in (payload.get("data_freshness") or {}).items() if (info or {}).get("status") == "stale"],
    )


def signal_freshness_summary(payload: dict[str, Any]) -> dict[str, Any]:
    freshness = dict(payload.get("data_freshness") or {})
    for source in payload.get("data_sources_used", []):
        freshness.setdefault(source, {"status": "present"})
    for source in payload.get("missing_data_sources", []):
        freshness.setdefault(source, {"status": "missing"})
    return freshness


def missing_signal_impact(missing_sources: list[str]) -> list[dict[str, str]]:
    return [
        {
            "source": source,
            "impact": "Lowers confidence and limits how strongly AI1SAD should interpret the score.",
        }
        for source in missing_sources
    ]


def active_rules_from_factors(factors: list[dict[str, Any]]) -> list[str]:
    rules = []
    for factor in factors:
        points = float(factor.get("points", 0) or 0)
        if points > 0 and factor.get("factor"):
            rules.append(str(factor["factor"]))
    return sorted(set(rules))


def suppression_reasons(payload: dict[str, Any]) -> list[str]:
    reasons = []
    warning_score = _score(payload, "warning_score")
    surveillance_score = _score(payload, "surveillance_priority_score", "priority_score")
    activity_score = _score(payload, "activity_hazard_score", "activity_context_score")
    if warning_score < 25:
        reasons.append("General environmental warning remains low because live-condition signals are not strongly stacked.")
    if surveillance_score >= 75 and warning_score < 25:
        reasons.append("Low general warning does not suppress surveillance priority when activity, habitat, or species context is strong.")
    if max(warning_score, surveillance_score, activity_score) < 45:
        reasons.append("Weak alert conditions should be suppressed unless recent sightings, incidents, or biological events are present.")
    if payload.get("quiet_day_comparison", {}).get("band_change") is False:
        reasons.append("Quiet-day comparison does not show a warning-band change.")
    return reasons


def recommendation_key(payload: dict[str, Any]) -> str:
    factors = {str(item.get("factor", "")).lower() for item in payload.get("dominant_factors", [])}
    pattern = str(payload.get("recommended_pattern", "")).lower()
    alert_type = str(payload.get("alert_type", "")).lower()
    if "carcass" in " ".join(factors) or alert_type == "biological_event":
        return "carcass_event_buffer_zone"
    if "sighting" in " ".join(factors) or alert_type == "sighting_cluster":
        return "post_sighting_focus_area"
    if "reef" in pattern or any("reef" in factor or "dropoff" in factor for factor in factors):
        return "reef_edge_expanding_grid"
    if "inlet" in " ".join(factors) or "river" in " ".join(factors) or "surf-zone" in pattern:
        return "inlet_surf_zone_scan"
    if _score(payload, "surveillance_priority_score", "priority_score") < 25:
        return "low_priority_observation"
    return "shoreline_parallel_sweep"


def operational_interpretation(payload: dict[str, Any]) -> str:
    warning_score = _score(payload, "warning_score")
    surveillance_score = _score(payload, "surveillance_priority_score", "priority_score")
    activity_score = _score(payload, "activity_hazard_score", "activity_context_score")
    if surveillance_score >= 75 and warning_score < 25:
        return (
            "AI1SAD reads this as low general environmental warning but high operational surveillance priority. "
            "That split is driven by activity, habitat, regional species suitability, or recent operational context."
        )
    if warning_score >= 70:
        return "Environmental/live-condition signals are elevated and should be reviewed with local safety, weather, and wildlife guidance."
    if activity_score >= 45:
        return "Activity context is the main driver; use activity-specific caution without treating this as attack probability."
    return "Current signals support routine observation unless new environmental, biological, sighting, or activity signals arrive."


def build_explanation(
    payload: dict[str, Any],
    *,
    output_type: str,
    location: dict[str, Any] | None = None,
    replay: bool = False,
) -> dict[str, Any]:
    zone = payload.get("zones", [{}])[0] if payload.get("zones") else payload
    warning = payload.get("warning", {})
    if isinstance(warning, dict) and warning:
        base = {**warning, **zone}
    else:
        base = dict(zone)
    for key in [
        "active_pack",
        "available_pack",
        "pack_features_used",
        "pack_notice",
        "data_freshness",
        "missing_data_sources",
        "data_sources_used",
        "quiet_day_comparison",
    ]:
        if key in payload and key not in base:
            base[key] = payload[key]

    dominant = list(base.get("dominant_factors", []))
    contributions = factor_contributions(dominant, _score(base, "surveillance_priority_score", "priority_score", "warning_score"))
    rec_key = recommendation_key(base)
    recommendation = RECOMMENDATION_PATTERNS[rec_key]
    missing = list(base.get("missing_data_sources", []))

    return {
        "output_type": output_type,
        "location": _location(base, location),
        "active_pack": base.get("active_pack", payload.get("active_pack", "core")),
        "available_pack": base.get("available_pack", payload.get("available_pack")),
        "pack_notice": base.get("pack_notice", payload.get("pack_notice")),
        "pack_features_used": base.get("pack_features_used", payload.get("pack_features_used", [])),
        "warning_score": _score(base, "warning_score"),
        "activity_hazard_score": _score(base, "activity_hazard_score", "activity_context_score"),
        "surveillance_priority_score": _score(base, "surveillance_priority_score", "priority_score"),
        "dominant_factors": dominant,
        "factor_contributions": contributions,
        "confidence_breakdown": confidence_breakdown(base),
        "data_freshness": signal_freshness_summary(base),
        "missing_data_sources": missing,
        "missing_signal_impact": missing_signal_impact(missing),
        "regional_pack_influence": {
            "active_pack": base.get("active_pack", payload.get("active_pack", "core")),
            "available_pack": base.get("available_pack", payload.get("available_pack")),
            "features_used": base.get("pack_features_used", payload.get("pack_features_used", [])),
            "notice": base.get("pack_notice", payload.get("pack_notice")),
        },
        "regional_rules_triggered": active_rules_from_factors(dominant),
        "active_rules_triggered": active_rules_from_factors(dominant),
        "suppression_reasons": suppression_reasons(base),
        "operational_interpretation": operational_interpretation(base),
        "recommended_action": recommendation["recommended_action"],
        "recommended_surveillance_pattern": rec_key,
        "recommended_surveillance_pattern_label": recommendation["label"],
        "metadata": model_metadata(replay=replay),
        "disclaimer": AI1SAD_API_DISCLAIMER,
    }


def attach_alert_explanation_summary(alert: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(alert)
    explanation = build_explanation(enriched, output_type="alert")
    enriched.setdefault("recommended_action", explanation["recommended_action"])
    enriched["explanation_summary"] = {
        "operational_interpretation": explanation["operational_interpretation"],
        "recommended_surveillance_pattern": explanation["recommended_surveillance_pattern"],
        "dominant_factors": explanation["factor_contributions"][:5],
        "confidence_breakdown": explanation["confidence_breakdown"],
        "metadata": explanation["metadata"],
        "disclaimer": explanation["disclaimer"],
    }
    return enriched
