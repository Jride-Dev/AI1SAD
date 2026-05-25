from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


BIOLOGICAL_EVENT_TYPES = {
    "biological_event",
    "carcass",
    "whale_carcass",
    "seal_presence",
    "sea_lion_presence",
    "sea_turtle_nesting",
    "sea_turtle_migration",
    "baitfish_presence",
    "fish_kill",
    "seabird_hatchling_event",
}


HIGH_IMPACT_EVENT_TYPES = {"carcass", "whale_carcass", "fish_kill"}


STATIC_BIOLOGICAL_EVENTS: list[dict[str, Any]] = [
    {
        "event_id": "hawaii_turtle_season_tiger_context",
        "name": "Hawaii turtle-season tiger shark context",
        "signal_type": "sea_turtle_nesting",
        "species": "tiger shark",
        "lat": 21.315,
        "lon": -157.8,
        "value": 0.55,
        "confidence": 0.58,
        "impact": "contextual",
        "duration_hours": 720,
        "risk_factors": ["turtle_season", "tiger_shark_context", "migration_nesting_context"],
        "source_notes": "Static ecological context only; no live agency feed or scraping.",
        "pack_id": "hawaii",
    },
    {
        "event_id": "florida_baitfish_blacktip_overlap",
        "name": "Florida baitfish / blacktip overlap context",
        "signal_type": "baitfish_presence",
        "species": "blacktip shark",
        "lat": 27.7,
        "lon": -80.2,
        "value": 0.68,
        "confidence": 0.6,
        "impact": "contextual",
        "duration_hours": 96,
        "risk_factors": ["baitfish_presence", "blacktip_overlap", "prey_context"],
        "source_notes": "Static seasonal prey-overlap context only; no live scraping.",
        "pack_id": "florida",
    },
    {
        "event_id": "south_africa_seal_colony_white_shark_context",
        "name": "South Africa seal colony / white shark context",
        "signal_type": "seal_presence",
        "species": "white shark",
        "lat": -34.205,
        "lon": 18.45,
        "value": 0.62,
        "confidence": 0.62,
        "impact": "contextual",
        "duration_hours": 720,
        "risk_factors": ["seal_presence", "white_shark_context", "pinniped_prey_context"],
        "source_notes": "Static seal-colony context only; no live wildlife feed.",
        "pack_id": "south_africa",
    },
    {
        "event_id": "red_sea_carcass_dumping_anomaly_context",
        "name": "Red Sea carcass or dumping anomaly context",
        "signal_type": "carcass",
        "species": "oceanic whitetip shark",
        "lat": 20.5,
        "lon": 38.5,
        "value": 0.9,
        "confidence": 0.7,
        "impact": "high",
        "duration_hours": 72,
        "risk_factors": ["carcass", "feeding_event_sensitivity", "nearshore_attractant"],
        "source_notes": "Manual/static example for reviewed carcass/dumping anomaly workflows; no live scraping.",
        "pack_id": "red_sea",
    },
    {
        "event_id": "wa_reef_prey_context",
        "name": "Western Australia reef prey context",
        "signal_type": "biological_event",
        "species": "white shark",
        "lat": -31.983,
        "lon": 115.515,
        "value": 0.5,
        "confidence": 0.54,
        "impact": "contextual",
        "duration_hours": 168,
        "risk_factors": ["reef_prey_context", "white_shark_context"],
        "source_notes": "Static reef/prey context only; no live agency feed.",
        "pack_id": "western_australia",
    },
]


class BiologicalEventsProvider:
    provider_name = "biological_events_static"
    dataset = "static_manual_biological_events"

    def __init__(self, *, events: list[dict[str, Any]] | None = None) -> None:
        self.events = events or STATIC_BIOLOGICAL_EVENTS

    def matching_events(self, *, lat: float, lon: float, radius_km: float = 50) -> list[dict[str, Any]]:
        matches = []
        for event in self.events:
            distance = haversine_km(lon, lat, float(event["lon"]), float(event["lat"]))
            if distance <= radius_km:
                matches.append({**event, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: item["distance_km"])

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 50, lookback_hours: int = 168) -> list[ProviderSignal]:
        now = utc_now()
        signals: list[ProviderSignal] = []
        for event in self.matching_events(lat=lat, lon=lon, radius_km=radius_km):
            signal_type = str(event.get("signal_type", "biological_event"))
            if signal_type not in BIOLOGICAL_EVENT_TYPES:
                signal_type = "biological_event"
            duration_hours = int(event.get("duration_hours") or default_duration_hours(signal_type))
            timestamp = event.get("timestamp")
            observed_at = _parse_timestamp(timestamp) if timestamp else now
            expires_at = _parse_timestamp(event.get("expires_at")) or observed_at + timedelta(hours=duration_hours)
            location = {"name": event["name"], "geo": {"type": "Point", "coordinates": [event["lon"], event["lat"]]}}
            metadata = {
                "event_id": event["event_id"],
                "event_name": event["name"],
                "impact": event.get("impact", "contextual"),
                "pack_id": event.get("pack_id"),
                "source_notes": event.get("source_notes"),
                "distance_km": event["distance_km"],
                "duration_hours": duration_hours,
            }
            signal = ProviderSignal(
                signal_type=signal_type,
                timestamp=observed_at,
                expires_at=expires_at,
                location=location,
                provider=self.provider_name,
                confidence=float(event.get("confidence", 0.55)),
                species=event.get("species"),
                value=float(event.get("value", 0.5)),
                units="index",
                dataset=self.dataset,
                risk_factors=list(event.get("risk_factors", ["biological_event"])),
                relevance_score=relevance_for_event(signal_type, float(event.get("value", 0.5)), float(event.get("confidence", 0.55))),
            )
            object.__setattr__(signal, "value_metadata", metadata)
            signals.append(signal)
        return signals

    def fetch_normalized_signals(self, **kwargs: Any) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(**kwargs)]
        for signal in normalized:
            metadata = signal.get("value_metadata", {})
            signal["provider_timestamp"] = signal["timestamp"]
            signal["event_type"] = signal["signal_type"]
            signal["event_id"] = metadata.get("event_id")
            signal["event_name"] = metadata.get("event_name")
            signal["event_impact"] = metadata.get("impact")
            signal["pack_id"] = metadata.get("pack_id")
            signal["source_notes"] = metadata.get("source_notes")
            signal["distance_km"] = metadata.get("distance_km")
            signal["duration_hours"] = metadata.get("duration_hours")
        return normalized


def default_duration_hours(signal_type: str) -> int:
    if signal_type in HIGH_IMPACT_EVENT_TYPES:
        return 72
    if signal_type in {"baitfish_presence", "seabird_hatchling_event"}:
        return 96
    if signal_type in {"sea_turtle_nesting", "sea_turtle_migration", "seal_presence", "sea_lion_presence"}:
        return 720
    return 168


def relevance_for_event(signal_type: str, value: float, confidence: float) -> float:
    base = 0.65 if signal_type in HIGH_IMPACT_EVENT_TYPES else 0.42
    return round(min(0.9, base + value * 0.15 + confidence * 0.1), 3)


def normalize_static_biological_events(
    *,
    lat: float,
    lon: float,
    radius_km: float = 50,
    lookback_hours: int = 168,
    events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return BiologicalEventsProvider(events=events).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, events: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_events = events or STATIC_BIOLOGICAL_EVENTS
    return {
        "_id": "biological_events_static",
        "provider": "biological_events_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "event_count": len(active_events),
        "mode": "static_manual_offline",
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=utc_now().tzinfo)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=utc_now().tzinfo)
    except ValueError:
        return None
