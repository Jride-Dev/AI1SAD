from __future__ import annotations

from app.providers.base import ProviderSignal, ProviderUnavailable


class NewsEventsProvider:
    provider_name = "news_events"

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        raise ProviderUnavailable("News/event search is a placeholder and must be reviewed before public ingestion.")
