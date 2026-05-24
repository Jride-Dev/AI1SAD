from __future__ import annotations

from app.providers.base import ProviderSignal


class ManualEventsProvider:
    provider_name = "manual_events"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        return []
