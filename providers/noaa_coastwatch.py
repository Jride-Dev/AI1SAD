from __future__ import annotations

from typing import Any


def fetch_sst(_lat: float, _lon: float) -> dict[str, Any]:
    return {
        "provider": "noaa_coastwatch",
        "status": "not_configured",
        "reason": "ERDDAP SST placeholder. Configure dataset ID, spatial buffer, and time window before enabling.",
    }

