from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class NoaaCoastwatchProvider:
    provider_name = "noaa_coastwatch"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("NOAA CoastWatch ERDDAP adapter is a placeholder until dataset IDs are configured.")
