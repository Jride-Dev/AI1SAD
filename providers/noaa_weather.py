from __future__ import annotations

from typing import Any


def fetch_alerts_and_observations(_lat: float, _lon: float) -> dict[str, Any]:
    return {
        "provider": "noaa_weather",
        "status": "not_configured",
        "reason": "NWS alerts/observations interface placeholder. Add station/zone resolution before enabling.",
    }

