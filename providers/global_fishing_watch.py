from __future__ import annotations

from typing import Any


def fetch_vessel_activity(_lat: float, _lon: float) -> dict[str, Any]:
    return {
        "provider": "global_fishing_watch",
        "status": "not_configured",
        "reason": "Global Fishing Watch placeholder. API credentials must come from .env/deployment secrets.",
    }

