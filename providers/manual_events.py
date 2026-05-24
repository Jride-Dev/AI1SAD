from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_manual_event(
    *,
    event_type: str,
    lat: float,
    lon: float,
    description: str,
    visibility: str = "public",
    observed_at: str | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "visibility": visibility,
        "description": description,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "location": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
        "provider": "manual_events",
    }

