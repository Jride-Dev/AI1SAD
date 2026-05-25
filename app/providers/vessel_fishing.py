from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


VESSEL_FISHING_SIGNAL_TYPES = {
    "vessel_activity",
    "fishing_activity",
    "commercial_fishing_pressure",
    "recreational_fishing_pressure",
    "spearfishing_activity",
    "pier_fishing_pressure",
    "marina_boat_pressure",
    "dive_boat_activity",
    "liveaboard_activity",
}


SHORT_HIGH_IMPACT_TYPES = {"fishing_activity", "spearfishing_activity", "commercial_fishing_pressure", "recreational_fishing_pressure"}
MEDIUM_CONTEXT_TYPES = {"dive_boat_activity", "liveaboard_activity", "vessel_activity"}
LONG_BASELINE_TYPES = {"pier_fishing_pressure", "marina_boat_pressure"}


STATIC_VESSEL_FISHING_SIGNALS: list[dict[str, Any]] = [
    {
        "signal_id": "florida_inlet_pier_recreational_fishing",
        "name": "Florida piers/inlets recreational fishing context",
        "signal_type": "pier_fishing_pressure",
        "lat": 27.7,
        "lon": -80.2,
        "value": 0.72,
        "confidence": 0.6,
        "duration_hours": 168,
        "risk_factors": ["pier_fishing", "inlet_fishing", "recreational_fishing_pressure"],
        "source_notes": "Static/manual Florida pier and inlet fishing-pressure context; no AIS or live API feed.",
        "pack_id": "florida",
    },
    {
        "signal_id": "wa_reef_spearfishing_context",
        "name": "Western Australia reef spearfishing context",
        "signal_type": "spearfishing_activity",
        "lat": -31.983,
        "lon": 115.515,
        "value": 0.88,
        "confidence": 0.62,
        "duration_hours": 24,
        "risk_factors": ["spearfishing_activity", "reef_fishing_context", "white_shark_search_context"],
        "source_notes": "Static/manual reef and spearfishing context; no AIS, MarineTraffic, or Global Fishing Watch call.",
        "pack_id": "western_australia",
    },
    {
        "signal_id": "red_sea_liveaboard_dive_corridor",
        "name": "Red Sea liveaboard and dive boat tourism corridor context",
        "signal_type": "liveaboard_activity",
        "lat": 27.915,
        "lon": 34.33,
        "value": 0.68,
        "confidence": 0.54,
        "duration_hours": 72,
        "risk_factors": ["liveaboard_activity", "dive_boat_activity", "tourism_corridor"],
        "source_notes": "Static/manual Red Sea dive tourism corridor context; no live vessel tracking.",
        "pack_id": "red_sea",
    },
    {
        "signal_id": "south_africa_fishing_seal_colony_coastline",
        "name": "South Africa fishing and seal-colony coastline context",
        "signal_type": "commercial_fishing_pressure",
        "lat": -34.205,
        "lon": 18.45,
        "value": 0.58,
        "confidence": 0.56,
        "duration_hours": 36,
        "risk_factors": ["commercial_fishing_pressure", "seal_colony_coastline_context"],
        "source_notes": "Static/manual fishing-pressure context near seal-colony coastline; no live provider calls.",
        "pack_id": "south_africa",
    },
    {
        "signal_id": "hawaii_nearshore_recreational_fishing",
        "name": "Hawaii nearshore recreational fishing context",
        "signal_type": "recreational_fishing_pressure",
        "lat": 21.315,
        "lon": -157.8,
        "value": 0.5,
        "confidence": 0.52,
        "duration_hours": 36,
        "risk_factors": ["nearshore_recreational_fishing", "tiger_shark_context"],
        "source_notes": "Static/manual nearshore fishing context; no live vessel or social feed.",
        "pack_id": "hawaii",
    },
]


class VesselFishingProvider:
    provider_name = "vessel_fishing_static"
    dataset = "static_manual_vessel_fishing_signals"

    def __init__(self, *, signals: list[dict[str, Any]] | None = None) -> None:
        self.signals = signals or STATIC_VESSEL_FISHING_SIGNALS

    def matching_signals(self, *, lat: float, lon: float, radius_km: float = 50) -> list[dict[str, Any]]:
        matches = []
        for signal in self.signals:
            distance = haversine_km(lon, lat, float(signal["lon"]), float(signal["lat"]))
            if distance <= radius_km:
                matches.append({**signal, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: item["distance_km"])

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 50, lookback_hours: int = 72) -> list[ProviderSignal]:
        now = utc_now()
        provider_signals: list[ProviderSignal] = []
        for item in self.matching_signals(lat=lat, lon=lon, radius_km=radius_km):
            signal_type = str(item.get("signal_type", "vessel_activity"))
            if signal_type not in VESSEL_FISHING_SIGNAL_TYPES:
                signal_type = "vessel_activity"
            duration_hours = int(item.get("duration_hours") or default_duration_hours(signal_type))
            timestamp = _parse_timestamp(item.get("timestamp")) or now
            expires_at = _parse_timestamp(item.get("expires_at")) or timestamp + timedelta(hours=duration_hours)
            value = float(item.get("value", 0.5))
            confidence = float(item.get("confidence", 0.55))
            location = {"name": item["name"], "geo": {"type": "Point", "coordinates": [item["lon"], item["lat"]]}}
            metadata = {
                "signal_id": item["signal_id"],
                "signal_name": item["name"],
                "activity_type": signal_type,
                "pack_id": item.get("pack_id"),
                "source_notes": item.get("source_notes"),
                "distance_km": item["distance_km"],
                "duration_hours": duration_hours,
            }
            signal = ProviderSignal(
                signal_type=signal_type,
                timestamp=timestamp,
                expires_at=expires_at,
                location=location,
                provider=self.provider_name,
                confidence=confidence,
                value=value,
                units="index",
                dataset=self.dataset,
                risk_factors=list(item.get("risk_factors", [signal_type])),
                relevance_score=relevance_for_signal(signal_type, value, confidence),
            )
            object.__setattr__(signal, "value_metadata", metadata)
            provider_signals.append(signal)
        return provider_signals

    def fetch_normalized_signals(self, **kwargs: Any) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(**kwargs)]
        for signal in normalized:
            metadata = signal.get("value_metadata", {})
            signal["provider_timestamp"] = signal["timestamp"]
            signal["activity_type"] = metadata.get("activity_type", signal["signal_type"])
            signal["signal_id"] = metadata.get("signal_id")
            signal["signal_name"] = metadata.get("signal_name")
            signal["pack_id"] = metadata.get("pack_id")
            signal["source_notes"] = metadata.get("source_notes")
            signal["distance_km"] = metadata.get("distance_km")
            signal["duration_hours"] = metadata.get("duration_hours")
        return normalized


def default_duration_hours(signal_type: str) -> int:
    if signal_type in SHORT_HIGH_IMPACT_TYPES:
        return 24
    if signal_type in MEDIUM_CONTEXT_TYPES:
        return 72
    if signal_type in LONG_BASELINE_TYPES:
        return 168
    return 48


def relevance_for_signal(signal_type: str, value: float, confidence: float) -> float:
    if signal_type == "spearfishing_activity":
        base = 0.68
    elif signal_type in {"fishing_activity", "commercial_fishing_pressure", "recreational_fishing_pressure"}:
        base = 0.55
    else:
        base = 0.38
    return round(min(0.88, base + value * 0.14 + confidence * 0.08), 3)


def normalize_static_vessel_fishing_signals(
    *,
    lat: float,
    lon: float,
    radius_km: float = 50,
    lookback_hours: int = 72,
    signals: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return VesselFishingProvider(signals=signals).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, signals: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_signals = signals or STATIC_VESSEL_FISHING_SIGNALS
    return {
        "_id": "vessel_fishing_static",
        "provider": "vessel_fishing_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "signal_count": len(active_signals),
        "mode": "static_manual_offline",
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
