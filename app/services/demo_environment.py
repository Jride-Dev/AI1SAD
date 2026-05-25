from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.disclaimers import AI1SAD_API_DISCLAIMER


DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "horseshoe_reef_2026",
        "label": "Horseshoe Reef 2026 surveillance replay",
        "region": "Western Australia",
        "context": "Low general warning with high surveillance priority from spearfishing, reef habitat, and white shark regional context.",
        "activity_context": "spearfishing",
        "public_case_study": "docs/CASE_STUDY_HORSESHOE_REEF_2026.md",
    },
    {
        "scenario_id": "queensland_spearfishing_reef_tiger_bull_2026",
        "label": "Queensland Spearfishing 2026 replay",
        "region": "Far North Queensland, Australia",
        "context": "Tropical reef spearfishing context with tiger/bull shark operational suitability.",
        "activity_context": "spearfishing",
        "public_case_study": "docs/case_studies/queensland_spearfishing_2026.md",
    },
    {
        "scenario_id": "florida_crowded_beach_inlet",
        "label": "Florida crowded beach and inlet context",
        "region": "Florida",
        "context": "Crowding, inlet/runoff, surf/fishing exposure, and blacktip/bull regional context for operational review.",
        "activity_context": "swimming/surfing/fishing",
        "public_case_study": None,
    },
    {
        "scenario_id": "hawaii_october_tiger_context",
        "label": "Hawaii October tiger shark context",
        "region": "Hawaii",
        "context": "October regional attention window with tiger shark context and bounded environmental interpretation.",
        "activity_context": "general water activity",
        "public_case_study": None,
    },
    {
        "scenario_id": "red_sea_anomaly_context",
        "label": "Red Sea anomaly context",
        "region": "Red Sea",
        "context": "Carcass/shipping/tourism anomaly context for advisory and surveillance review.",
        "activity_context": "diving/tourism corridor",
        "public_case_study": None,
    },
]


def demo_metadata(enabled: bool) -> dict[str, Any]:
    return {
        "demo_mode": enabled,
        "demo_label": "AI1SAD controlled public demo" if enabled else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": AI1SAD_API_DISCLAIMER,
    }


def annotate_demo_response(payload: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return payload
    response = dict(payload)
    response["demo"] = demo_metadata(True)
    return response


def demo_status(*, enabled: bool, mongodb_configured: bool, database_name: str) -> dict[str, Any]:
    return {
        "demo_mode": enabled,
        "mode": "demo" if enabled else "live",
        "database_configured": mongodb_configured,
        "database": database_name if mongodb_configured else None,
        "admin_writes_enabled": False if enabled else "environment-controlled",
        "private_internal_data_exposed": False,
        "live_providers_enabled_by_default": False,
        "billing_enabled": False,
        "authentication_enabled": False,
        "scoring_behavior": "unchanged",
        "disclaimer": AI1SAD_API_DISCLAIMER,
    }


def demo_scenarios(*, enabled: bool) -> dict[str, Any]:
    return {
        "demo_mode": enabled,
        "private_internal_data_exposed": False,
        "scenarios": DEMO_SCENARIOS,
        "disclaimer": AI1SAD_API_DISCLAIMER,
    }
