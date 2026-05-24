from __future__ import annotations

from app.providers.base import ProviderSignal, utc_now


class OpenMeteoProvider:
    provider_name = "open_meteo"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        return [
            ProviderSignal(
                signal_type="weather_rainfall",
                timestamp=utc_now(),
                location={"geo": {"type": "Point", "coordinates": [lon, lat]}},
                provider=self.provider_name,
                confidence=0.75,
                dataset="open_meteo_archive",
                risk_factors=["rainfall_runoff"],
                relevance_score=0.65,
            )
        ]
