from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


HUMAN_EXPOSURE_PROFILES: list[dict[str, Any]] = [
    {
        "profile_id": "clearwater_beach",
        "name": "Clearwater Beach",
        "lat": 27.977,
        "lon": -82.828,
        "baseline_exposure": 0.78,
        "peak_season_months": [3, 4, 5, 6, 7, 8],
        "weekend_multiplier": 1.18,
        "holiday_multiplier": 1.3,
        "parking_crowd_notes": "High tourism pressure, parking constraints, and strong weekend beach use.",
        "source_notes": "Static profile from known public beach-use seasonality; no live scraping.",
        "confidence": 0.62,
        "pack_id": "florida",
    },
    {
        "profile_id": "south_beach_miami",
        "name": "South Beach Miami",
        "lat": 25.782,
        "lon": -80.131,
        "baseline_exposure": 0.86,
        "peak_season_months": [2, 3, 4, 5, 6, 7, 12],
        "weekend_multiplier": 1.15,
        "holiday_multiplier": 1.28,
        "parking_crowd_notes": "Dense urban tourism, events, and beach crowding.",
        "source_notes": "Static profile from public tourism/beach-use patterns; no live scraping.",
        "confidence": 0.64,
        "pack_id": "florida",
    },
    {
        "profile_id": "daytona_beach",
        "name": "Daytona Beach",
        "lat": 29.210,
        "lon": -81.023,
        "baseline_exposure": 0.72,
        "peak_season_months": [3, 4, 5, 6, 7, 8],
        "weekend_multiplier": 1.16,
        "holiday_multiplier": 1.26,
        "parking_crowd_notes": "Large beach capacity with event and holiday surges.",
        "source_notes": "Static profile from public beach/event seasonality; no live scraping.",
        "confidence": 0.6,
        "pack_id": "florida",
    },
    {
        "profile_id": "new_smyrna_beach",
        "name": "New Smyrna Beach",
        "lat": 29.025,
        "lon": -80.926,
        "baseline_exposure": 0.68,
        "peak_season_months": [3, 4, 5, 6, 7, 8, 9],
        "weekend_multiplier": 1.17,
        "holiday_multiplier": 1.25,
        "parking_crowd_notes": "Surf and beach-use pressure increases on weekends and holidays.",
        "source_notes": "Static profile from public beach-use patterns; no live scraping.",
        "confidence": 0.62,
        "pack_id": "florida",
    },
    {
        "profile_id": "virginia_beach",
        "name": "Virginia Beach",
        "lat": 36.852,
        "lon": -75.978,
        "baseline_exposure": 0.7,
        "peak_season_months": [5, 6, 7, 8, 9],
        "weekend_multiplier": 1.18,
        "holiday_multiplier": 1.32,
        "parking_crowd_notes": "Seasonal resort beach with strong summer and holiday crowding.",
        "source_notes": "Static profile from public tourism seasonality; no live scraping.",
        "confidence": 0.58,
        "pack_id": "us_east_coast",
    },
    {
        "profile_id": "rehoboth_beach",
        "name": "Rehoboth Beach",
        "lat": 38.716,
        "lon": -75.077,
        "baseline_exposure": 0.64,
        "peak_season_months": [5, 6, 7, 8, 9],
        "weekend_multiplier": 1.22,
        "holiday_multiplier": 1.34,
        "parking_crowd_notes": "Small resort town with parking and beach crowd pressure in summer.",
        "source_notes": "Static profile from public tourism seasonality; no live scraping.",
        "confidence": 0.56,
        "pack_id": "us_east_coast",
    },
    {
        "profile_id": "hampton_beach",
        "name": "Hampton Beach",
        "lat": 42.908,
        "lon": -70.812,
        "baseline_exposure": 0.6,
        "peak_season_months": [6, 7, 8],
        "weekend_multiplier": 1.23,
        "holiday_multiplier": 1.35,
        "parking_crowd_notes": "Short summer season with strong weekend and holiday pressure.",
        "source_notes": "Static profile from public tourism seasonality; no live scraping.",
        "confidence": 0.54,
        "pack_id": "us_east_coast",
    },
    {
        "profile_id": "hurghada",
        "name": "Hurghada",
        "lat": 27.257,
        "lon": 33.812,
        "baseline_exposure": 0.72,
        "peak_season_months": [4, 5, 6, 7, 8, 9, 10],
        "weekend_multiplier": 1.08,
        "holiday_multiplier": 1.22,
        "parking_crowd_notes": "Tourism and diving/snorkeling pressure around resort beaches and boats.",
        "source_notes": "Static Red Sea tourism profile; no live scraping.",
        "confidence": 0.52,
        "pack_id": "red_sea",
    },
    {
        "profile_id": "sharm_el_sheikh",
        "name": "Sharm El-Sheikh",
        "lat": 27.915,
        "lon": 34.330,
        "baseline_exposure": 0.74,
        "peak_season_months": [4, 5, 6, 7, 8, 9, 10],
        "weekend_multiplier": 1.07,
        "holiday_multiplier": 1.24,
        "parking_crowd_notes": "Resort, reef, diving, and snorkeling exposure pressure.",
        "source_notes": "Static Red Sea tourism profile; no live scraping.",
        "confidence": 0.52,
        "pack_id": "red_sea",
    },
    {
        "profile_id": "rottnest_island",
        "name": "Rottnest Island",
        "lat": -32.006,
        "lon": 115.516,
        "baseline_exposure": 0.5,
        "peak_season_months": [12, 1, 2, 3],
        "weekend_multiplier": 1.18,
        "holiday_multiplier": 1.32,
        "parking_crowd_notes": "Seasonal ferry tourism, beaches, diving, fishing, and boating exposure.",
        "source_notes": "Static Western Australia tourism profile; no live scraping.",
        "confidence": 0.56,
        "pack_id": "western_australia",
    },
]


class HumanExposureProvider:
    provider_name = "human_exposure_static"
    dataset = "static_beach_exposure_profiles"

    def __init__(self, *, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or HUMAN_EXPOSURE_PROFILES

    def matching_profiles(self, *, lat: float, lon: float, radius_km: float = 25) -> list[dict[str, Any]]:
        matches = []
        for profile in self.profiles:
            distance = haversine_km(lon, lat, float(profile["lon"]), float(profile["lat"]))
            if distance <= radius_km:
                matches.append({**profile, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: item["distance_km"])

    def fetch_signals(
        self,
        *,
        lat: float,
        lon: float,
        radius_km: float = 25,
        lookback_hours: int = 72,
        month: int | None = None,
        weekend: bool = False,
        holiday: bool = False,
        event: bool = False,
    ) -> list[ProviderSignal]:
        now = utc_now()
        expires_at = now + timedelta(hours=24)
        signals: list[ProviderSignal] = []
        for profile in self.matching_profiles(lat=lat, lon=lon, radius_km=radius_km):
            exposure = float(profile["baseline_exposure"])
            peak = bool(month and month in profile.get("peak_season_months", []))
            if peak:
                exposure *= 1.12
            if weekend:
                exposure *= float(profile.get("weekend_multiplier", 1.0))
            if holiday:
                exposure *= float(profile.get("holiday_multiplier", 1.0))
            if event:
                exposure *= 1.18
            exposure = round(max(0.0, min(1.0, exposure)), 3)
            location = {"name": profile["name"], "geo": {"type": "Point", "coordinates": [profile["lon"], profile["lat"]]}}
            metadata = {
                "profile_id": profile["profile_id"],
                "profile_name": profile["name"],
                "pack_id": profile.get("pack_id"),
                "parking_crowd_notes": profile.get("parking_crowd_notes"),
                "source_notes": profile.get("source_notes"),
                "distance_km": profile["distance_km"],
            }
            signals.append(self._signal("human_exposure", now, expires_at, location, exposure, profile, ["human_exposure"], metadata))
            if exposure >= 0.7:
                signals.append(self._signal("beach_crowd_pressure", now, expires_at, location, exposure, profile, ["crowded_beach"], metadata))
            if "parking" in str(profile.get("parking_crowd_notes", "")).lower() and exposure >= 0.6:
                signals.append(self._signal("parking_pressure", now, expires_at, location, min(1.0, exposure * 0.9), profile, ["parking_pressure"], metadata))
            if peak:
                signals.append(self._signal("tourism_season", now, expires_at, location, min(1.0, exposure), profile, ["tourism_season"], metadata))
            if weekend:
                signals.append(self._signal("weekend_exposure", now, expires_at, location, min(1.0, exposure), profile, ["weekend_exposure"], metadata))
            if holiday:
                signals.append(self._signal("holiday_exposure", now, expires_at, location, min(1.0, exposure), profile, ["holiday_exposure"], metadata))
            if event:
                signals.append(self._signal("event_exposure", now, expires_at, location, min(1.0, exposure), profile, ["event_exposure"], metadata))
        return signals

    def fetch_normalized_signals(self, **kwargs: Any) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(**kwargs)]
        for signal in normalized:
            metadata = signal.get("value_metadata", {})
            signal["provider_timestamp"] = signal["timestamp"]
            signal["exposure_index"] = signal["value"]
            signal["exposure_level"] = exposure_level(float(signal["value"] or 0))
            signal["profile_id"] = metadata.get("profile_id")
            signal["profile_name"] = metadata.get("profile_name")
            signal["pack_id"] = metadata.get("pack_id")
            signal["parking_crowd_notes"] = metadata.get("parking_crowd_notes")
            signal["source_notes"] = metadata.get("source_notes")
            signal["distance_km"] = metadata.get("distance_km")
        return normalized

    def _signal(
        self,
        signal_type: str,
        timestamp: datetime,
        expires_at: datetime,
        location: dict[str, Any],
        value: float,
        profile: dict[str, Any],
        factors: list[str],
        metadata: dict[str, Any],
    ) -> ProviderSignal:
        signal = ProviderSignal(
            signal_type=signal_type,
            timestamp=timestamp,
            expires_at=expires_at,
            location=location,
            provider=self.provider_name,
            confidence=float(profile.get("confidence", 0.5)),
            value=value,
            units="index",
            dataset=self.dataset,
            risk_factors=factors,
            relevance_score=min(0.75, 0.35 + value * 0.35),
        )
        object.__setattr__(signal, "value_metadata", metadata)
        return signal


def normalize_static_human_exposure(
    *,
    lat: float,
    lon: float,
    radius_km: float = 25,
    month: int | None = None,
    weekend: bool = False,
    holiday: bool = False,
    event: bool = False,
    profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return HumanExposureProvider(profiles=profiles).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        month=month,
        weekend=weekend,
        holiday=holiday,
        event=event,
    )


def exposure_level(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.6:
        return "moderate"
    if value >= 0.35:
        return "low"
    return "minimal"


def provider_health_document(*, profiles: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_profiles = profiles or HUMAN_EXPOSURE_PROFILES
    return {
        "_id": "human_exposure_static",
        "provider": "human_exposure_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "profile_count": len(active_profiles),
        "mode": "static_offline",
    }
