from __future__ import annotations

from typing import Any


def search_marine_events(_lat: float, _lon: float) -> dict[str, Any]:
    return {
        "provider": "news_events",
        "status": "not_configured",
        "events": [],
        "reason": "Placeholder for whale carcass, stranding, baitfish bloom, and marine mortality event search.",
    }

