from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class NoaaNwsProvider:
    provider_name = "noaa_nws"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("NOAA/NWS observations and alert adapter is a placeholder.")
