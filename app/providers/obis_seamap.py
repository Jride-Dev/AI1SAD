from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class ObisSeamapProvider:
    provider_name = "obis_seamap"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("OBIS-SEAMAP species occurrence adapter is a placeholder pending API policy review.")
