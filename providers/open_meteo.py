from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_previous_72h(lat: float, lon: float, timeout: int = 10) -> dict[str, Any]:
    """Fetch no-key Open-Meteo rainfall/temp signals for the previous 72 hours."""
    params = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": "rain,temperature_2m",
            "past_days": 3,
            "forecast_days": 1,
            "timezone": "UTC",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    with urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rain_values = payload.get("hourly", {}).get("rain", [])[-72:]
    temp_values = payload.get("hourly", {}).get("temperature_2m", [])[-72:]
    return {
        "provider": "open_meteo",
        "status": "ok",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "rainfall_72h_mm": round(sum(value or 0 for value in rain_values), 2),
        "air_temp_c_latest": next((value for value in reversed(temp_values) if value is not None), None),
        "source_url": url,
    }

