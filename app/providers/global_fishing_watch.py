from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class GlobalFishingWatchProvider:
    provider_name = "global_fishing_watch"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("Global Fishing Watch adapter is a placeholder; API credentials must stay in deployment secrets.")
