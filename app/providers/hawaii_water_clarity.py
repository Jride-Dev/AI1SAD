from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


HAWAII_WATER_CLARITY_SIGNAL_TYPES = {
    "water_clarity_context",
    "turbidity_context",
    "sediment_runoff_visibility_context",
    "surf_zone_visibility_context",
}


STATIC_HAWAII_WATER_CLARITY_PROFILES: list[dict[str, Any]] = [
    {
        "id": "oahu_cromwells_visibility_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Cromwell's Beach / Diamond Head visibility baseline",
        "lat": 21.255,
        "lon": -157.81,
        "clarity_class": "variable",
        "turbidity_class": "low_to_moderate",
        "runoff_visibility_context": "urban_south_shore_runoff_possible",
        "surf_zone_visibility_context": "surf_zone_glare_and_swell_variability",
        "confidence": 0.5,
        "preferred_source": "NOAA CoastWatch ocean color products",
        "fallback_sources": ["PacIOOS water-quality products", "Hawaii beach water-quality datasets"],
        "source_url_reference": "https://coastwatch.noaa.gov/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["water_clarity_context", "turbidity_context", "sediment_runoff_visibility_context", "surf_zone_visibility_context"],
        "source_notes": "Static/offline visibility baseline profile; not a live turbidity or water-quality observation.",
    },
    {
        "id": "oahu_waikiki_ala_moana_visibility_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Waikiki / Ala Moana visibility baseline",
        "lat": 21.278,
        "lon": -157.838,
        "clarity_class": "variable_urban_nearshore",
        "turbidity_class": "moderate",
        "runoff_visibility_context": "urban_runoff_and_harbor_influence_possible",
        "surf_zone_visibility_context": "high_human_exposure_surf_zone_visibility_variability",
        "confidence": 0.48,
        "preferred_source": "PacIOOS water-quality products",
        "fallback_sources": ["NOAA CoastWatch ocean color products", "Hawaii beach water-quality datasets"],
        "source_url_reference": "https://www.pacioos.hawaii.edu/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["water_clarity_context", "turbidity_context", "sediment_runoff_visibility_context", "surf_zone_visibility_context"],
        "source_notes": "Static/offline urban south-shore visibility baseline only.",
    },
    {
        "id": "oahu_sandy_bottom_clear_quiet_baseline",
        "region": "Oahu south shore, Hawaii",
        "island": "Oahu",
        "location_name": "Oahu sandy-bottom clearer quiet-day visibility baseline",
        "lat": 21.27,
        "lon": -157.85,
        "clarity_class": "clearer_quiet_baseline",
        "turbidity_class": "low",
        "runoff_visibility_context": "low_runoff_visibility_context",
        "surf_zone_visibility_context": "quiet_day_reference_visibility",
        "confidence": 0.52,
        "preferred_source": "Hawaii beach water-quality datasets",
        "fallback_sources": ["NOAA CoastWatch ocean color products"],
        "source_url_reference": "https://health.hawaii.gov/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["water_clarity_context", "surf_zone_visibility_context"],
        "source_notes": "Quiet-day static/offline visibility baseline only.",
    },
]


def _signal_value(profile: dict[str, Any], signal_type: str) -> float:
    turbidity = str(profile.get("turbidity_class", "")).lower()
    clarity = str(profile.get("clarity_class", "")).lower()
    value = 0.25
    if "moderate" in turbidity:
        value += 0.18
    if "variable" in clarity:
        value += 0.08
    if signal_type == "sediment_runoff_visibility_context":
        value += 0.1
    if signal_type == "water_clarity_context" and "clearer" in clarity:
        value -= 0.08
    return round(max(0.08, min(0.7, value)), 3)


def _relevance(signal_type: str, confidence: float) -> float:
    base = {
        "water_clarity_context": 0.34,
        "turbidity_context": 0.5,
        "sediment_runoff_visibility_context": 0.48,
        "surf_zone_visibility_context": 0.42,
    }.get(signal_type, 0.35)
    return round(min(0.76, base + confidence * 0.08), 3)


class HawaiiWaterClarityProvider:
    provider_name = "hawaii_water_clarity_static"
    dataset = "static_hawaii_water_clarity_baseline"

    def __init__(self, *, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or STATIC_HAWAII_WATER_CLARITY_PROFILES

    def matching_profiles(self, *, lat: float, lon: float, radius_km: float = 35) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for profile in self.profiles:
            distance = haversine_km(lon, lat, float(profile["lon"]), float(profile["lat"]))
            if distance <= radius_km:
                matches.append({**profile, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: item["distance_km"])

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 35, lookback_hours: int = 2160) -> list[ProviderSignal]:
        now = utc_now()
        signals: list[ProviderSignal] = []
        for profile in self.matching_profiles(lat=lat, lon=lon, radius_km=radius_km):
            source_date = _parse_timestamp(profile.get("source_date")) or now - timedelta(days=365 * 6)
            expires_at = now + timedelta(days=3650)
            confidence = max(0.32, min(0.68, float(profile.get("confidence", 0.5) or 0.5)))
            for signal_type in profile.get("signal_types", []):
                if signal_type not in HAWAII_WATER_CLARITY_SIGNAL_TYPES:
                    continue
                metadata = {
                    "id": profile["id"],
                    "region": profile.get("region"),
                    "island": profile.get("island"),
                    "location_name": profile.get("location_name"),
                    "clarity_class": profile.get("clarity_class"),
                    "turbidity_class": profile.get("turbidity_class"),
                    "runoff_visibility_context": profile.get("runoff_visibility_context"),
                    "surf_zone_visibility_context": profile.get("surf_zone_visibility_context"),
                    "preferred_source": profile.get("preferred_source"),
                    "fallback_sources": profile.get("fallback_sources", []),
                    "source_url_reference": profile.get("source_url_reference"),
                    "source_notes": profile.get("source_notes"),
                    "source_date": profile.get("source_date"),
                    "data_freshness": profile.get("data_freshness", "static_baseline_candidate"),
                    "baseline_only": True,
                    "pack_id": profile.get("pack_id", "hawaii"),
                    "distance_km": profile.get("distance_km"),
                }
                signal = ProviderSignal(
                    signal_type=signal_type,
                    timestamp=source_date,
                    expires_at=expires_at,
                    location={"name": profile.get("location_name"), "geo": {"type": "Point", "coordinates": [profile["lon"], profile["lat"]]}},
                    provider=self.provider_name,
                    confidence=confidence,
                    species=None,
                    value=_signal_value(profile, signal_type),
                    units="visibility_context_index",
                    dataset=self.dataset,
                    risk_factors=[signal_type, "hawaii_static_water_clarity_baseline"],
                    visibility=str(profile.get("visibility", "public")),
                    relevance_score=_relevance(signal_type, confidence),
                )
                object.__setattr__(signal, "value_metadata", metadata)
                signals.append(signal)
        return signals

    def fetch_normalized_signals(self, **kwargs: Any) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(**kwargs)]
        for signal in normalized:
            metadata = signal.get("value_metadata", {})
            signal["provider_timestamp"] = signal["timestamp"]
            signal["water_clarity_profile_id"] = metadata.get("id")
            signal["region"] = metadata.get("region")
            signal["island"] = metadata.get("island")
            signal["location_name"] = metadata.get("location_name")
            signal["clarity_class"] = metadata.get("clarity_class")
            signal["turbidity_class"] = metadata.get("turbidity_class")
            signal["runoff_visibility_context"] = metadata.get("runoff_visibility_context")
            signal["surf_zone_visibility_context"] = metadata.get("surf_zone_visibility_context")
            signal["preferred_source"] = metadata.get("preferred_source")
            signal["fallback_sources"] = metadata.get("fallback_sources", [])
            signal["source_url_reference"] = metadata.get("source_url_reference")
            signal["source_date"] = metadata.get("source_date")
            signal["data_freshness_label"] = metadata.get("data_freshness")
            signal["baseline_only"] = True
            signal["pack_id"] = metadata.get("pack_id")
            signal["distance_km"] = metadata.get("distance_km")
        return normalized


def normalize_static_hawaii_water_clarity_signals(
    *,
    lat: float,
    lon: float,
    radius_km: float = 35,
    lookback_hours: int = 2160,
    profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return HawaiiWaterClarityProvider(profiles=profiles).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, profiles: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_profiles = profiles or STATIC_HAWAII_WATER_CLARITY_PROFILES
    return {
        "_id": "hawaii_water_clarity_static",
        "provider": "hawaii_water_clarity_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "profile_count": len(active_profiles),
        "mode": "static_manual_offline",
        "freshness_note": "Static/offline water clarity and turbidity baseline context only; do not treat as live water-quality or ocean-color observations.",
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
