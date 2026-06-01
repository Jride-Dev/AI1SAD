from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


HAWAII_HABITAT_SIGNAL_TYPES = {
    "reef_channel_habitat",
    "shallow_reef_habitat",
    "reef_edge_habitat",
    "hardbottom_habitat",
    "submerged_vegetation_habitat",
    "sandy_bottom_habitat",
    "dropoff_habitat",
    "nearshore_structure_context",
    "habitat_visibility_context",
}


STATIC_HAWAII_HABITAT_PROFILES: list[dict[str, Any]] = [
    {
        "id": "oahu_cromwells_diamond_head_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Cromwell's Beach / Diamond Head nearshore baseline",
        "lat": 21.255,
        "lon": -157.81,
        "polygon_reference": "oahu_diamond_head_nearshore_sector_a",
        "habitat_type": "reef_edge",
        "geomorphology_type": "fringing_reef_and_dropoff_transition",
        "biological_cover_type": "mixed_hardbottom_and_patch_reef",
        "depth_band_m": "3-18",
        "edge_context": "moderate_reef_edge_transition",
        "channel_context": "adjacent_channel_influence",
        "visibility_context": "variable_nearshore_visibility",
        "confidence": 0.58,
        "source_name": "NOAA NCCOS Oahu shallow-water benthic habitat maps",
        "source_url_reference": "https://coastalscience.noaa.gov/",
        "source_date": "2012-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["reef_edge_habitat", "dropoff_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "source_notes": "Historic/static benthic baseline context only; not a live field observation.",
    },
    {
        "id": "oahu_kaikoo_hale_mano_channel_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Kaikoo / Hale Mano channel context baseline",
        "lat": 21.258,
        "lon": -157.805,
        "polygon_reference": "oahu_kaikoo_channel_sector_b",
        "habitat_type": "reef_channel",
        "geomorphology_type": "channel_cut_through_reef_platform",
        "biological_cover_type": "mixed_reef_hardbottom",
        "depth_band_m": "5-22",
        "edge_context": "defined_channel_edge",
        "channel_context": "pronounced_channel_geometry",
        "visibility_context": "channel_variability_context",
        "confidence": 0.56,
        "source_name": "Pacific Islands Benthic Habitat Mapping Center Oahu resources",
        "source_url_reference": "https://www.soest.hawaii.edu/pibhmc/",
        "source_date": "2011-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["reef_channel_habitat", "reef_edge_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "source_notes": "Historic/static mapped channel context only.",
    },
    {
        "id": "oahu_waikiki_ala_moana_baseline",
        "region": "Honolulu, Oahu, Hawaii",
        "island": "Oahu",
        "location_name": "Waikiki / Ala Moana south-shore baseline",
        "lat": 21.278,
        "lon": -157.838,
        "polygon_reference": "oahu_waikiki_ala_moana_sector_c",
        "habitat_type": "shallow_reef",
        "geomorphology_type": "reef_flat_and_nearshore_structure",
        "biological_cover_type": "reef_algae_hardbottom_mix",
        "depth_band_m": "1-12",
        "edge_context": "broad_reef_flat_edge",
        "channel_context": "localized_channel_gaps",
        "visibility_context": "urban_nearshore_variable_visibility",
        "confidence": 0.55,
        "source_name": "Hawaii Statewide GIS benthic habitat baseline layer",
        "source_url_reference": "https://planning.hawaii.gov/gis/",
        "source_date": "2010-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["shallow_reef_habitat", "hardbottom_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "source_notes": "Statewide historic baseline layer; retain source date in metadata.",
    },
    {
        "id": "oahu_reef_channel_demo_baseline",
        "region": "Oahu south shore, Hawaii",
        "island": "Oahu",
        "location_name": "Oahu reef-channel demo baseline profile",
        "lat": 21.24,
        "lon": -157.79,
        "polygon_reference": "oahu_reef_channel_demo_sector_d",
        "habitat_type": "reef_channel",
        "geomorphology_type": "channel_and_dropoff_mosaic",
        "biological_cover_type": "patch_reef_and_hardbottom",
        "depth_band_m": "4-20",
        "edge_context": "high_channel_edge_contrast",
        "channel_context": "strong_channel_presence",
        "visibility_context": "channel_turbidity_variability",
        "confidence": 0.52,
        "source_name": "NOAA NCCOS / PIBHMC baseline synthesis",
        "source_notes": "Static composite demo profile assembled from documented baseline maps.",
        "source_date": "2011-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["reef_channel_habitat", "dropoff_habitat", "nearshore_structure_context", "habitat_visibility_context"],
    },
    {
        "id": "oahu_shallow_reef_edge_demo_baseline",
        "region": "Oahu south shore, Hawaii",
        "island": "Oahu",
        "location_name": "Oahu shallow-reef edge demo baseline profile",
        "lat": 21.266,
        "lon": -157.82,
        "polygon_reference": "oahu_shallow_reef_edge_demo_sector_e",
        "habitat_type": "shallow_reef_edge",
        "geomorphology_type": "fringing_reef_edge",
        "biological_cover_type": "reef_algae_coral_mix",
        "depth_band_m": "2-10",
        "edge_context": "moderate_edge_structure",
        "channel_context": "minor_channel_presence",
        "visibility_context": "shallow_glint_and_swell_variability",
        "confidence": 0.53,
        "source_name": "Hawaii Statewide GIS benthic habitat baseline layer",
        "source_date": "2010-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["shallow_reef_habitat", "reef_edge_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "source_notes": "Static baseline profile only.",
    },
    {
        "id": "oahu_sandy_bottom_quiet_day_baseline",
        "region": "Oahu south shore, Hawaii",
        "island": "Oahu",
        "location_name": "Oahu sandy-bottom quiet-day baseline profile",
        "lat": 21.27,
        "lon": -157.85,
        "polygon_reference": "oahu_sandy_bottom_quiet_day_sector_f",
        "habitat_type": "sandy_bottom",
        "geomorphology_type": "open_nearshore_sand_plain",
        "biological_cover_type": "low_structure_sand_dominant",
        "depth_band_m": "2-14",
        "edge_context": "minimal_edge_structure",
        "channel_context": "limited_channel_expression",
        "visibility_context": "typically_clearer_open_sand_context",
        "confidence": 0.5,
        "source_name": "NOAA NCCOS Oahu shallow-water benthic habitat maps",
        "source_date": "2012-01-01",
        "data_freshness": "historic_static_baseline",
        "baseline_only": True,
        "pack_id": "hawaii",
        "visibility": "public",
        "signal_types": ["sandy_bottom_habitat", "nearshore_structure_context", "habitat_visibility_context"],
        "source_notes": "Quiet-day comparison baseline context only.",
    },
]


def _habitat_value(profile: dict[str, Any], signal_type: str) -> float:
    habitat = str(profile.get("habitat_type", ""))
    channel_bonus = 0.12 if "channel" in habitat or signal_type == "reef_channel_habitat" else 0.0
    edge_bonus = 0.08 if "edge" in habitat or signal_type == "reef_edge_habitat" else 0.0
    sandy_penalty = -0.1 if signal_type == "sandy_bottom_habitat" else 0.0
    return round(max(0.1, min(0.9, 0.35 + channel_bonus + edge_bonus + sandy_penalty)), 3)


def _relevance(signal_type: str, confidence: float) -> float:
    base = {
        "reef_channel_habitat": 0.56,
        "reef_edge_habitat": 0.52,
        "shallow_reef_habitat": 0.46,
        "dropoff_habitat": 0.5,
        "hardbottom_habitat": 0.42,
        "submerged_vegetation_habitat": 0.4,
        "sandy_bottom_habitat": 0.28,
        "nearshore_structure_context": 0.44,
        "habitat_visibility_context": 0.38,
    }.get(signal_type, 0.35)
    return round(min(0.82, base + confidence * 0.08), 3)


class HawaiiHabitatProvider:
    provider_name = "hawaii_habitat_static"
    dataset = "static_hawaii_benthic_baseline"

    def __init__(self, *, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or STATIC_HAWAII_HABITAT_PROFILES

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
            source_date = _parse_timestamp(profile.get("source_date")) or now - timedelta(days=365 * 10)
            expires_at = now + timedelta(days=3650)
            confidence = max(0.35, min(0.75, float(profile.get("confidence", 0.52) or 0.52)))
            for signal_type in profile.get("signal_types", []):
                if signal_type not in HAWAII_HABITAT_SIGNAL_TYPES:
                    continue
                metadata = {
                    "id": profile["id"],
                    "region": profile.get("region"),
                    "island": profile.get("island"),
                    "location_name": profile.get("location_name"),
                    "polygon_reference": profile.get("polygon_reference"),
                    "habitat_type": profile.get("habitat_type"),
                    "geomorphology_type": profile.get("geomorphology_type"),
                    "biological_cover_type": profile.get("biological_cover_type"),
                    "depth_band_m": profile.get("depth_band_m"),
                    "edge_context": profile.get("edge_context"),
                    "channel_context": profile.get("channel_context"),
                    "visibility_context": profile.get("visibility_context"),
                    "source_name": profile.get("source_name"),
                    "source_url_reference": profile.get("source_url_reference"),
                    "source_notes": profile.get("source_notes"),
                    "source_date": profile.get("source_date"),
                    "data_freshness": profile.get("data_freshness", "historic_static_baseline"),
                    "baseline_only": True,
                    "pack_id": profile.get("pack_id", "hawaii"),
                    "distance_km": profile.get("distance_km"),
                    "visibility_context_public": profile.get("visibility_context"),
                }
                signal = ProviderSignal(
                    signal_type=signal_type,
                    timestamp=source_date,
                    expires_at=expires_at,
                    location={"name": profile.get("location_name"), "geo": {"type": "Point", "coordinates": [profile["lon"], profile["lat"]]}},
                    provider=self.provider_name,
                    confidence=confidence,
                    species=None,
                    value=_habitat_value(profile, signal_type),
                    units="habitat_context_index",
                    dataset=self.dataset,
                    risk_factors=[signal_type, "hawaii_historic_benthic_baseline"],
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
            signal["habitat_profile_id"] = metadata.get("id")
            signal["region"] = metadata.get("region")
            signal["island"] = metadata.get("island")
            signal["location_name"] = metadata.get("location_name")
            signal["polygon_reference"] = metadata.get("polygon_reference")
            signal["habitat_type"] = metadata.get("habitat_type")
            signal["geomorphology_type"] = metadata.get("geomorphology_type")
            signal["biological_cover_type"] = metadata.get("biological_cover_type")
            signal["depth_band_m"] = metadata.get("depth_band_m")
            signal["edge_context"] = metadata.get("edge_context")
            signal["channel_context"] = metadata.get("channel_context")
            signal["visibility_context"] = metadata.get("visibility_context_public")
            signal["source_name"] = metadata.get("source_name")
            signal["source_url_reference"] = metadata.get("source_url_reference")
            signal["source_date"] = metadata.get("source_date")
            signal["data_freshness_label"] = metadata.get("data_freshness")
            signal["baseline_only"] = True
            signal["pack_id"] = metadata.get("pack_id")
            signal["distance_km"] = metadata.get("distance_km")
        return normalized


def normalize_static_hawaii_habitat_signals(
    *,
    lat: float,
    lon: float,
    radius_km: float = 35,
    lookback_hours: int = 2160,
    profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return HawaiiHabitatProvider(profiles=profiles).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, profiles: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_profiles = profiles or STATIC_HAWAII_HABITAT_PROFILES
    return {
        "_id": "hawaii_habitat_static",
        "provider": "hawaii_habitat_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "profile_count": len(active_profiles),
        "mode": "static_manual_offline",
        "freshness_note": "Historic/static benthic baseline context only; do not treat as current conditions.",
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
