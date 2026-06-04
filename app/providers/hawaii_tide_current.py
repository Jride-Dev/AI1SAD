from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


HAWAII_TIDE_CURRENT_SIGNAL_TYPES = {
    "tide_state_context",
    "tide_window_context",
    "nearshore_current_context",
    "current_direction_context",
    "current_speed_context",
    "channel_flow_context",
    "tidal_exchange_context",
}


STATIC_HAWAII_TIDE_CURRENT_PROFILES: list[dict[str, Any]] = [
    {
        "id": "oahu_cromwells_south_shore_roms_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Cromwell's Beach / Diamond Head nearshore water-movement baseline",
        "lat": 21.255,
        "lon": -157.81,
        "model_domain": "south_shore_oahu",
        "preferred_source": "PacIOOS South Shore Oahu ROMS",
        "fallback_sources": ["PacIOOS Oahu ROMS", "PacIOOS Main Hawaiian Islands ROMS"],
        "supporting_station_source": "NOAA CO-OPS Honolulu-area tide/current station data",
        "source_url_reference": "https://www.pacioos.hawaii.edu/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "tide_state": "changing_tide_window",
        "tide_window": "early_morning_transition_context",
        "nearshore_current_direction": "alongshore_variable",
        "nearshore_current_speed_class": "moderate",
        "channel_flow_context": "reef_channel_exchange_possible",
        "current_convergence_context": "reef_channel_convergence_possible",
        "tidal_exchange_context": "bounded_exchange_context",
        "nearshore_model_resolution": "preferred_south_shore_nearshore",
        "forecast_freshness": "static_not_live",
        "station_coverage_gap": "station_support_not_microchannel_observation",
        "regional_fallback_used": False,
        "confidence": 0.58,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["tide_state_context", "tide_window_context", "nearshore_current_context", "current_direction_context", "current_speed_context", "channel_flow_context", "tidal_exchange_context"],
        "source_notes": "Static/offline baseline profile; not a live PacIOOS or NOAA CO-OPS observation.",
    },
    {
        "id": "oahu_waikiki_ala_moana_current_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Waikiki / Ala Moana south-shore water-movement baseline",
        "lat": 21.278,
        "lon": -157.838,
        "model_domain": "south_shore_oahu",
        "preferred_source": "PacIOOS South Shore Oahu ROMS",
        "fallback_sources": ["PacIOOS Oahu ROMS", "PacIOOS Main Hawaiian Islands ROMS"],
        "supporting_station_source": "NOAA CO-OPS Honolulu-area tide/current station data",
        "source_url_reference": "https://www.pacioos.hawaii.edu/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "tide_state": "urban_south_shore_tide_window",
        "tide_window": "tourism_corridor_transition_context",
        "nearshore_current_direction": "alongshore_and_channel_variable",
        "nearshore_current_speed_class": "low_to_moderate",
        "channel_flow_context": "localized_channel_exchange_possible",
        "current_convergence_context": "localized_convergence_possible",
        "tidal_exchange_context": "bounded_exchange_context",
        "nearshore_model_resolution": "preferred_south_shore_nearshore",
        "forecast_freshness": "static_not_live",
        "station_coverage_gap": "station_support_not_local_surf_line_observation",
        "regional_fallback_used": False,
        "confidence": 0.55,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["tide_state_context", "nearshore_current_context", "current_direction_context", "channel_flow_context"],
        "source_notes": "Static/offline baseline profile; operational use requires live source ingestion later.",
    },
    {
        "id": "oahu_sandy_bottom_quiet_tide_baseline",
        "region": "Oahu south shore, Hawaii",
        "island": "Oahu",
        "location_name": "Oahu sandy-bottom quiet water-movement baseline",
        "lat": 21.27,
        "lon": -157.85,
        "model_domain": "oahu",
        "preferred_source": "PacIOOS Oahu ROMS",
        "fallback_sources": ["PacIOOS Main Hawaiian Islands ROMS"],
        "supporting_station_source": "NOAA CO-OPS tide/current station data where applicable",
        "source_url_reference": "https://www.pacioos.hawaii.edu/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "tide_state": "general_tide_window",
        "tide_window": "quiet_day_reference_context",
        "nearshore_current_direction": "weak_variable",
        "nearshore_current_speed_class": "low",
        "channel_flow_context": "limited_channel_expression",
        "current_convergence_context": "none",
        "tidal_exchange_context": "low_exchange_context",
        "nearshore_model_resolution": "oahu_nearshore_fallback",
        "forecast_freshness": "static_not_live",
        "station_coverage_gap": "station_support_generalized",
        "regional_fallback_used": False,
        "confidence": 0.5,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["tide_state_context", "nearshore_current_context", "current_speed_context"],
        "source_notes": "Quiet-day static/offline baseline profile.",
    },
    {
        "id": "main_hawaiian_islands_roms_fallback_baseline",
        "region": "Main Hawaiian Islands",
        "island": "Multi-island",
        "location_name": "Main Hawaiian Islands ROMS fallback water-movement baseline",
        "lat": 21.3,
        "lon": -157.9,
        "model_domain": "main_hawaiian_islands",
        "preferred_source": "PacIOOS Main Hawaiian Islands ROMS",
        "fallback_sources": [],
        "supporting_station_source": "NOAA CO-OPS station data where available",
        "source_url_reference": "https://www.pacioos.hawaii.edu/",
        "source_date": "2018-01-01",
        "data_freshness": "static_baseline_candidate",
        "baseline_only": True,
        "tide_state": "regional_tide_window",
        "tide_window": "fallback_model_context",
        "nearshore_current_direction": "regional_variable",
        "nearshore_current_speed_class": "low",
        "channel_flow_context": "not_location_specific",
        "current_convergence_context": "not_location_specific",
        "tidal_exchange_context": "coarse_regional_context",
        "nearshore_model_resolution": "regional_fallback_coarse",
        "forecast_freshness": "static_not_live",
        "station_coverage_gap": "regional_station_gap",
        "regional_fallback_used": True,
        "confidence": 0.42,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["tide_state_context", "nearshore_current_context"],
        "source_notes": "Coarse static fallback only; prefer South Shore Oahu ROMS for south-shore Oahu operations.",
    },
]


def _source_rank(profile: dict[str, Any]) -> int:
    source = str(profile.get("preferred_source", "")).lower()
    if "south shore oahu" in source:
        return 0
    if "oahu roms" in source:
        return 1
    if "main hawaiian islands" in source:
        return 2
    return 3


def _signal_value(profile: dict[str, Any], signal_type: str) -> float:
    speed = str(profile.get("nearshore_current_speed_class", "low"))
    channel = str(profile.get("channel_flow_context", ""))
    value = 0.3
    if "moderate" in speed:
        value += 0.15
    if "channel" in channel and "limited" not in channel and signal_type == "channel_flow_context":
        value += 0.18
    if signal_type in {"current_speed_context", "nearshore_current_context"}:
        value += 0.08
    if signal_type == "tidal_exchange_context":
        value += 0.06
    return round(max(0.1, min(0.75, value)), 3)


def _relevance(signal_type: str, confidence: float) -> float:
    base = {
        "tide_state_context": 0.34,
        "tide_window_context": 0.36,
        "nearshore_current_context": 0.5,
        "current_direction_context": 0.42,
        "current_speed_context": 0.44,
        "channel_flow_context": 0.56,
        "tidal_exchange_context": 0.46,
    }.get(signal_type, 0.35)
    return round(min(0.8, base + confidence * 0.08), 3)


class HawaiiTideCurrentProvider:
    provider_name = "hawaii_tide_current_static"
    dataset = "static_hawaii_tide_current_baseline"

    def __init__(self, *, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or STATIC_HAWAII_TIDE_CURRENT_PROFILES

    def matching_profiles(self, *, lat: float, lon: float, radius_km: float = 35) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for profile in self.profiles:
            distance = haversine_km(lon, lat, float(profile["lon"]), float(profile["lat"]))
            if distance <= radius_km:
                matches.append({**profile, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: (_source_rank(item), item["distance_km"]))

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 35, lookback_hours: int = 2160) -> list[ProviderSignal]:
        now = utc_now()
        signals: list[ProviderSignal] = []
        for profile in self.matching_profiles(lat=lat, lon=lon, radius_km=radius_km):
            source_date = _parse_timestamp(profile.get("source_date")) or now - timedelta(days=365 * 6)
            expires_at = now + timedelta(days=3650)
            confidence = max(0.32, min(0.7, float(profile.get("confidence", 0.5) or 0.5)))
            for signal_type in profile.get("signal_types", []):
                if signal_type not in HAWAII_TIDE_CURRENT_SIGNAL_TYPES:
                    continue
                metadata = {
                    "id": profile["id"],
                    "region": profile.get("region"),
                    "island": profile.get("island"),
                    "location_name": profile.get("location_name"),
                    "model_domain": profile.get("model_domain"),
                    "preferred_source": profile.get("preferred_source"),
                    "fallback_sources": profile.get("fallback_sources", []),
                    "supporting_station_source": profile.get("supporting_station_source"),
                    "source_url_reference": profile.get("source_url_reference"),
                    "source_notes": profile.get("source_notes"),
                    "source_date": profile.get("source_date"),
                    "data_freshness": profile.get("data_freshness", "static_baseline_candidate"),
                    "baseline_only": True,
                    "tide_state": profile.get("tide_state"),
                    "tide_window": profile.get("tide_window"),
                    "nearshore_current_direction": profile.get("nearshore_current_direction"),
                    "nearshore_current_speed_class": profile.get("nearshore_current_speed_class"),
                    "channel_flow_context": profile.get("channel_flow_context"),
                    "current_convergence_context": profile.get("current_convergence_context"),
                    "tidal_exchange_context": profile.get("tidal_exchange_context"),
                    "nearshore_model_resolution": profile.get("nearshore_model_resolution"),
                    "forecast_freshness": profile.get("forecast_freshness"),
                    "station_coverage_gap": profile.get("station_coverage_gap"),
                    "regional_fallback_used": bool(profile.get("regional_fallback_used", False)),
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
                    units="water_movement_context_index",
                    dataset=self.dataset,
                    risk_factors=[signal_type, "hawaii_static_tide_current_baseline"],
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
            signal["tide_current_profile_id"] = metadata.get("id")
            signal["region"] = metadata.get("region")
            signal["island"] = metadata.get("island")
            signal["location_name"] = metadata.get("location_name")
            signal["model_domain"] = metadata.get("model_domain")
            signal["preferred_source"] = metadata.get("preferred_source")
            signal["fallback_sources"] = metadata.get("fallback_sources", [])
            signal["supporting_station_source"] = metadata.get("supporting_station_source")
            signal["source_url_reference"] = metadata.get("source_url_reference")
            signal["source_date"] = metadata.get("source_date")
            signal["data_freshness_label"] = metadata.get("data_freshness")
            signal["baseline_only"] = True
            signal["tide_state"] = metadata.get("tide_state")
            signal["tide_window"] = metadata.get("tide_window")
            signal["nearshore_current_direction"] = metadata.get("nearshore_current_direction")
            signal["nearshore_current_speed_class"] = metadata.get("nearshore_current_speed_class")
            signal["channel_flow_context"] = metadata.get("channel_flow_context")
            signal["current_convergence_context"] = metadata.get("current_convergence_context")
            signal["tidal_exchange_context"] = metadata.get("tidal_exchange_context")
            signal["nearshore_model_resolution"] = metadata.get("nearshore_model_resolution")
            signal["forecast_freshness"] = metadata.get("forecast_freshness")
            signal["station_coverage_gap"] = metadata.get("station_coverage_gap")
            signal["regional_fallback_used"] = bool(metadata.get("regional_fallback_used", False))
            signal["pack_id"] = metadata.get("pack_id")
            signal["distance_km"] = metadata.get("distance_km")
        return normalized


def normalize_static_hawaii_tide_current_signals(
    *,
    lat: float,
    lon: float,
    radius_km: float = 35,
    lookback_hours: int = 2160,
    profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return HawaiiTideCurrentProvider(profiles=profiles).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, profiles: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_profiles = profiles or STATIC_HAWAII_TIDE_CURRENT_PROFILES
    return {
        "_id": "hawaii_tide_current_static",
        "provider": "hawaii_tide_current_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "profile_count": len(active_profiles),
        "mode": "static_manual_offline",
        "freshness_note": "Static/offline tide-current baseline context only; do not treat as live PacIOOS or NOAA CO-OPS observations.",
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
