from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderSignal:
    signal_type: str
    timestamp: datetime
    location: dict[str, Any]
    provider: str
    confidence: float = 0.5
    species: str | None = None
    value: Any = None
    units: str | None = None
    expires_at: datetime | None = None
    dataset: str | None = None
    risk_factors: list[str] = field(default_factory=list)
    relevance_score: float = 0.5
    visibility: str = "public"


class SignalProvider(Protocol):
    provider_name: str

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float, lookback_hours: int) -> list[ProviderSignal]:
        ...


class ProviderUnavailable(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
