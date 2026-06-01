from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.risk_model import haversine_km
from app.services.signal_broker import normalize_provider_signal


KELP_SIGNAL_TYPES = {
    "kelp_forest_presence",
    "kelp_density_context",
    "kelp_edge_habitat",
    "kelp_prey_overlap",
    "white_shark_kelp_hunting_context",
}

DENSITY_WEIGHTS = {
    "sparse": 0.2,
    "moderate": 0.45,
    "dense": 0.55,
    "optimal_edge": 0.78,
}


STATIC_KELP_FOREST_PROFILES: list[dict[str, Any]] = [
    {
        "profile_id": "central_california_white_shark_kelp_demo",
        "name": "Central California kelp and white shark habitat demo",
        "region": "Central California",
        "lat": 36.95,
        "lon": -122.05,
        "density_class": "optimal_edge",
        "canopy_confidence": 0.62,
        "data_freshness": "static_old",
        "known_prey_association": "pinniped haulouts and nearshore prey context",
        "pinniped_presence": True,
        "pinniped_context": "Regional pinniped prey association; no live colony observation.",
        "human_activity_overlap": "surfing, kayaking, diving, and nearshore recreation overlap in some areas.",
        "source_notes": "Static demonstration kelp habitat profile only; no live canopy API or scraping.",
        "pack_id": "core",
        "species": "white shark",
        "signal_types": ["kelp_forest_presence", "kelp_density_context", "kelp_edge_habitat", "kelp_prey_overlap", "white_shark_kelp_hunting_context"],
    },
    {
        "profile_id": "monterey_bay_central_coast_kelp_demo",
        "name": "Monterey Bay central coast kelp demo",
        "region": "Monterey Bay / Central Coast",
        "lat": 36.62,
        "lon": -121.92,
        "density_class": "moderate",
        "canopy_confidence": 0.58,
        "data_freshness": "static_old",
        "known_prey_association": "nearshore fish and pinniped context",
        "pinniped_presence": True,
        "pinniped_context": "Known regional pinniped context, static only.",
        "human_activity_overlap": "diving, kayaking, surfing, and beach recreation may overlap.",
        "source_notes": "Static demonstration profile; current canopy extent should be verified before operational use.",
        "pack_id": "core",
        "species": "white shark",
        "signal_types": ["kelp_forest_presence", "kelp_density_context", "kelp_prey_overlap"],
    },
    {
        "profile_id": "false_bay_seal_island_kelp_context",
        "name": "False Bay / Seal Island kelp context",
        "region": "South Africa False Bay",
        "lat": -34.14,
        "lon": 18.58,
        "density_class": "optimal_edge",
        "canopy_confidence": 0.56,
        "data_freshness": "static_old",
        "known_prey_association": "seal island and kelp-edge prey context",
        "pinniped_presence": True,
        "pinniped_context": "Seal Island context represented as static prey association.",
        "human_activity_overlap": "surfing, diving, and boating context can overlap regionally.",
        "source_notes": "Static habitat/prey association only; no live wildlife feed.",
        "pack_id": "south_africa",
        "species": "white shark",
        "signal_types": ["kelp_forest_presence", "kelp_edge_habitat", "kelp_prey_overlap", "white_shark_kelp_hunting_context"],
    },
    {
        "profile_id": "western_australia_reef_kelp_context",
        "name": "Western Australia reef and kelp context",
        "region": "Western Australia",
        "lat": -31.98,
        "lon": 115.51,
        "density_class": "sparse",
        "canopy_confidence": 0.42,
        "data_freshness": "static_old",
        "known_prey_association": "reef and temperate habitat context",
        "pinniped_presence": False,
        "pinniped_context": "No pinniped overlap asserted by this static profile.",
        "human_activity_overlap": "spearfishing and diving may overlap with reef/kelp habitat.",
        "source_notes": "Sparse/static reef-kelp context only; use reef and activity signals as stronger evidence.",
        "pack_id": "western_australia",
        "species": "white shark",
        "signal_types": ["kelp_forest_presence", "kelp_density_context"],
    },
    {
        "profile_id": "golden_rule_kelp_bed_demo",
        "name": "Golden rule kelp bed demo",
        "region": "Synthetic demo",
        "lat": 36.8,
        "lon": -122.2,
        "density_class": "dense",
        "canopy_confidence": 0.5,
        "data_freshness": "synthetic_demo",
        "known_prey_association": "synthetic prey overlap for testing bounded behavior",
        "pinniped_presence": True,
        "pinniped_context": "Synthetic demo context; not a real-world field observation.",
        "human_activity_overlap": "synthetic surfing/diving/spearfishing overlap for golden-rule tests.",
        "source_notes": "Clearly synthetic demo profile for model QA; not an operational source.",
        "pack_id": "core",
        "species": "white shark",
        "signal_types": ["kelp_forest_presence", "kelp_density_context", "kelp_prey_overlap"],
    },
]


class KelpForestProvider:
    provider_name = "kelp_forest_static"
    dataset = "static_manual_kelp_forest_profiles"

    def __init__(self, *, profiles: list[dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or STATIC_KELP_FOREST_PROFILES

    def matching_profiles(self, *, lat: float, lon: float, radius_km: float = 50) -> list[dict[str, Any]]:
        matches = []
        for profile in self.profiles:
            distance = haversine_km(lon, lat, float(profile["lon"]), float(profile["lat"]))
            if distance <= radius_km:
                matches.append({**profile, "distance_km": round(distance, 2)})
        return sorted(matches, key=lambda item: item["distance_km"])

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 50, lookback_hours: int = 720) -> list[ProviderSignal]:
        now = utc_now()
        signals: list[ProviderSignal] = []
        for profile in self.matching_profiles(lat=lat, lon=lon, radius_km=radius_km):
            density_class = str(profile.get("density_class", "sparse"))
            value = DENSITY_WEIGHTS.get(density_class, 0.2)
            confidence = float(profile.get("canopy_confidence", 0.45))
            timestamp = _parse_timestamp(profile.get("timestamp")) or now - timedelta(days=120)
            expires_at = _parse_timestamp(profile.get("expires_at")) or timestamp + timedelta(days=900)
            signal_types = [item for item in profile.get("signal_types", ["kelp_forest_presence"]) if item in KELP_SIGNAL_TYPES]
            for signal_type in signal_types:
                metadata = {
                    "profile_id": profile["profile_id"],
                    "profile_name": profile["name"],
                    "region": profile["region"],
                    "density_class": density_class,
                    "data_freshness": profile.get("data_freshness", "static_old"),
                    "known_prey_association": profile.get("known_prey_association"),
                    "pinniped_presence": bool(profile.get("pinniped_presence", False)),
                    "pinniped_context": profile.get("pinniped_context"),
                    "human_activity_overlap": profile.get("human_activity_overlap"),
                    "pack_id": profile.get("pack_id"),
                    "source_notes": profile.get("source_notes"),
                    "distance_km": profile["distance_km"],
                    "visibility_effect": "reduced_open_water_visibility" if density_class == "dense" else "contextual_habitat",
                }
                signal = ProviderSignal(
                    signal_type=signal_type,
                    timestamp=timestamp,
                    expires_at=expires_at,
                    location={"name": profile["name"], "geo": {"type": "Point", "coordinates": [profile["lon"], profile["lat"]]}},
                    provider=self.provider_name,
                    confidence=confidence,
                    species=profile.get("species"),
                    value=value,
                    units="habitat_index",
                    dataset=self.dataset,
                    risk_factors=[signal_type, density_class, "static_kelp_context"],
                    relevance_score=relevance_for_profile(signal_type, density_class, confidence, bool(profile.get("pinniped_presence", False))),
                )
                object.__setattr__(signal, "value_metadata", metadata)
                signals.append(signal)
        return signals

    def fetch_normalized_signals(self, **kwargs: Any) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(**kwargs)]
        for signal in normalized:
            metadata = signal.get("value_metadata", {})
            signal["provider_timestamp"] = signal["timestamp"]
            signal["profile_id"] = metadata.get("profile_id")
            signal["profile_name"] = metadata.get("profile_name")
            signal["region"] = metadata.get("region")
            signal["density_class"] = metadata.get("density_class")
            signal["canopy_confidence"] = signal.get("confidence")
            signal["known_prey_association"] = metadata.get("known_prey_association")
            signal["pinniped_presence"] = metadata.get("pinniped_presence")
            signal["pinniped_context"] = metadata.get("pinniped_context")
            signal["human_activity_overlap"] = metadata.get("human_activity_overlap")
            signal["pack_id"] = metadata.get("pack_id")
            signal["source_notes"] = metadata.get("source_notes")
            signal["distance_km"] = metadata.get("distance_km")
            signal["visibility_effect"] = metadata.get("visibility_effect")
        return normalized


def relevance_for_profile(signal_type: str, density_class: str, confidence: float, pinniped_presence: bool) -> float:
    base = 0.32
    if signal_type == "kelp_edge_habitat":
        base = 0.5
    elif signal_type == "kelp_prey_overlap":
        base = 0.54
    elif signal_type == "white_shark_kelp_hunting_context":
        base = 0.58
    density_boost = {"sparse": 0.02, "moderate": 0.07, "dense": 0.09, "optimal_edge": 0.16}.get(density_class, 0)
    prey_boost = 0.08 if pinniped_presence else 0
    return round(min(0.82, base + density_boost + confidence * 0.08 + prey_boost), 3)


def normalize_static_kelp_forest_signals(
    *,
    lat: float,
    lon: float,
    radius_km: float = 50,
    lookback_hours: int = 720,
    profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return KelpForestProvider(profiles=profiles).fetch_normalized_signals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )


def provider_health_document(*, profiles: list[dict[str, Any]] | None = None, generated_signals: int = 0) -> dict[str, Any]:
    active_profiles = profiles or STATIC_KELP_FOREST_PROFILES
    return {
        "_id": "kelp_forest_static",
        "provider": "kelp_forest_static",
        "status": "healthy",
        "last_success": utc_now(),
        "last_error": None,
        "records_ingested": generated_signals,
        "profile_count": len(active_profiles),
        "mode": "static_manual_offline",
        "freshness_note": "Static kelp profiles are habitat context and should not be over-trusted as current canopy observations.",
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
