from __future__ import annotations

from typing import Any


def fetch_ocean_signals(_lat: float, _lon: float) -> dict[str, Any]:
    return {
        "provider": "copernicus_marine",
        "status": "not_configured",
        "reason": "Copernicus Marine placeholder. Credentials and product IDs must come from .env/deployment secrets.",
    }

