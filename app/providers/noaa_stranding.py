from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class NoaaStrandingProvider:
    provider_name = "noaa_stranding"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("NOAA stranding event adapter is a placeholder pending source selection.")
