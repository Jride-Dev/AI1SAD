from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal
from app.services.warning_engine import parse_dt


DEFAULT_MAX_AGE_HOURS = {
    "weather_rainfall": 6,
    "ocean_sst": 24,
    "sst_anomaly": 48,
    "vessel_activity": 24,
    "fishing_activity": 24,
    "commercial_fishing_pressure": 24,
    "recreational_fishing_pressure": 24,
    "spearfishing_activity": 24,
    "pier_fishing_pressure": 168,
    "marina_boat_pressure": 168,
    "dive_boat_activity": 72,
    "liveaboard_activity": 72,
    "biological_event": 336,
    "carcass": 72,
    "whale_carcass": 72,
    "fish_kill": 72,
    "baitfish_presence": 96,
    "seal_presence": 720,
    "sea_lion_presence": 720,
    "sea_turtle_nesting": 720,
    "sea_turtle_migration": 720,
    "seabird_hatchling_event": 96,
    "kelp_forest_presence": 2160,
    "kelp_density_context": 2160,
    "kelp_edge_habitat": 2160,
    "kelp_prey_overlap": 2160,
    "white_shark_kelp_hunting_context": 2160,
    "migration_window": 720,
    "prey_presence": 72,
    "tourism_exposure": 168,
    "human_exposure": 24,
    "beach_crowd_pressure": 24,
    "parking_pressure": 24,
    "weekend_exposure": 24,
    "holiday_exposure": 24,
    "event_exposure": 24,
    "weather_alert": 6,
    "sea_surface_temperature": 24,
    "flood_alert": 6,
    "thunderstorm_alert": 6,
    "coastal_flood_alert": 6,
    "rip_current_alert": 6,
    "high_surf_alert": 6,
    "marine_warning": 6,
}


def freshness_for(timestamp: datetime, *, now: datetime | None = None, max_age_hours: float = 24) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    observed = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    age_hours = round((now - observed).total_seconds() / 3600, 2)
    if age_hours <= max_age_hours:
        status = "fresh"
    elif age_hours <= max_age_hours * 2:
        status = "stale"
    else:
        status = "expired"
    return {
        "status": status,
        "observed_at": observed,
        "received_at": now,
        "age_hours": age_hours,
        "max_age_hours": max_age_hours,
    }


def normalize_provider_signal(raw: ProviderSignal | dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    if isinstance(raw, ProviderSignal):
        document = {
            "signal_type": raw.signal_type,
            "species": raw.species,
            "location": raw.location,
            "timestamp": raw.timestamp,
            "expires_at": raw.expires_at,
            "confidence": raw.confidence,
            "source": {"provider": raw.provider, "dataset": raw.dataset},
            "risk_relevance": {"score": raw.relevance_score, "factors": raw.risk_factors},
            "visibility": raw.visibility,
            "value": raw.value,
            "units": raw.units,
        }
        if hasattr(raw, "value_metadata"):
            document["value_metadata"] = getattr(raw, "value_metadata")
    else:
        document = dict(raw)
        document.setdefault("source", {"provider": document.get("provider", "unknown")})
        document.setdefault("risk_relevance", {"score": document.get("relevance_score", 0.5), "factors": []})
        document.setdefault("visibility", "public")

    timestamp = parse_dt(document.get("timestamp")) or parse_dt(document.get("observed_at")) or datetime.now(timezone.utc)
    signal_type = str(document.get("signal_type", "unknown"))
    max_age_hours = float(document.get("max_age_hours", DEFAULT_MAX_AGE_HOURS.get(signal_type, 24)))
    document["timestamp"] = timestamp
    document["data_freshness"] = freshness_for(timestamp, now=now, max_age_hours=max_age_hours)
    document.setdefault("expires_at", timestamp + timedelta(hours=max_age_hours * 2))
    document.setdefault("confidence", 0.5)
    return document


def active_public_signals(signals: list[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    active = []
    for signal in signals:
        if signal.get("visibility", "public") != "public":
            continue
        expires_at = parse_dt(signal.get("expires_at"))
        if expires_at and expires_at < now:
            continue
        normalized = normalize_provider_signal(signal, now=now)
        if normalized["data_freshness"]["status"] != "expired":
            active.append(normalized)
    return active


def warning_inputs_from_signals(signals: list[dict[str, Any]]) -> dict[str, Any]:
    active = active_public_signals(signals)
    inputs: dict[str, Any] = {
        "rainfall_72h_mm": None,
        "sea_surface_temp_c": None,
        "sst_anomaly_c": None,
        "vessel_activity_index": None,
        "vessel_fishing_signals": [],
        "biological_events": [],
        "kelp_habitat_signals": [],
        "human_exposure_index": None,
        "weather_alerts": [],
        "weather_alert_score": 0,
        "provider_status": {},
        "data_freshness": {},
    }
    for signal in active:
        signal_type = signal.get("signal_type")
        freshness = signal.get("data_freshness", {})
        source = signal.get("source", {}).get("provider", signal_type)
        status = freshness.get("status", "unknown")
        inputs["provider_status"][source] = "stale" if status == "stale" else "ok"
        inputs["data_freshness"][source] = freshness
        value = signal.get("value")
        relevance = signal.get("risk_relevance", {}).get("score", 0)

        if signal_type == "weather_rainfall" and value is not None:
            inputs["rainfall_72h_mm"] = max(float(value), float(inputs["rainfall_72h_mm"] or 0))
        elif signal_type in {"ocean_sst", "sea_surface_temperature"} and value is not None:
            inputs["sea_surface_temp_c"] = float(value)
        elif signal_type == "sst_anomaly" and value is not None:
            inputs["sst_anomaly_c"] = float(value)
        elif signal_type in {
            "vessel_activity",
            "fishing_activity",
            "commercial_fishing_pressure",
            "recreational_fishing_pressure",
            "spearfishing_activity",
            "pier_fishing_pressure",
            "marina_boat_pressure",
            "dive_boat_activity",
            "liveaboard_activity",
        } and value is not None:
            inputs["vessel_activity_index"] = max(float(value), float(inputs["vessel_activity_index"] or 0))
            inputs["vessel_fishing_signals"].append(
                {
                    "visibility": "public",
                    "signal_type": signal_type,
                    "activity_type": signal.get("activity_type", signal_type),
                    "observed_at": signal.get("timestamp"),
                    "expires_at": signal.get("expires_at"),
                    "confidence": signal.get("confidence"),
                    "value": value,
                    "source": signal.get("source"),
                    "risk_relevance": signal.get("risk_relevance"),
                    "pack_id": signal.get("pack_id"),
                }
            )
        elif signal_type in {
            "biological_event",
            "prey_presence",
            "ecology_event",
            "carcass",
            "whale_carcass",
            "seal_presence",
            "sea_lion_presence",
            "sea_turtle_nesting",
            "sea_turtle_migration",
            "baitfish_presence",
            "fish_kill",
            "seabird_hatchling_event",
        }:
            event = {
                "visibility": "public",
                "event_type": signal_type,
                "observed_at": signal.get("timestamp"),
                "expires_at": signal.get("expires_at"),
                "confidence": signal.get("confidence"),
                "value": value,
                "species": signal.get("species"),
                "source": signal.get("source"),
                "risk_relevance": signal.get("risk_relevance"),
            }
            inputs["biological_events"].append(event)
        elif signal_type in {
            "kelp_forest_presence",
            "kelp_density_context",
            "kelp_edge_habitat",
            "kelp_prey_overlap",
            "white_shark_kelp_hunting_context",
        }:
            inputs["kelp_habitat_signals"].append(
                {
                    "visibility": "public",
                    "signal_type": signal_type,
                    "observed_at": signal.get("timestamp"),
                    "expires_at": signal.get("expires_at"),
                    "confidence": signal.get("confidence"),
                    "value": value,
                    "species": signal.get("species"),
                    "source": signal.get("source"),
                    "risk_relevance": signal.get("risk_relevance"),
                    "density_class": signal.get("density_class"),
                    "canopy_confidence": signal.get("canopy_confidence"),
                    "pinniped_presence": signal.get("pinniped_presence"),
                    "pinniped_context": signal.get("pinniped_context"),
                    "human_activity_overlap": signal.get("human_activity_overlap"),
                    "known_prey_association": signal.get("known_prey_association"),
                    "pack_id": signal.get("pack_id"),
                    "visibility_effect": signal.get("visibility_effect"),
                    "profile_id": signal.get("profile_id"),
                    "profile_name": signal.get("profile_name"),
                }
            )
        elif signal_type in {
            "tourism_exposure",
            "human_exposure",
            "beach_crowd_pressure",
            "parking_pressure",
            "weekend_exposure",
            "holiday_exposure",
            "event_exposure",
        } and value is not None:
            inputs["human_exposure_index"] = max(float(value), float(inputs["human_exposure_index"] or 0))
        elif signal_type in {
            "weather_alert",
            "flood_alert",
            "thunderstorm_alert",
            "coastal_flood_alert",
            "rip_current_alert",
            "high_surf_alert",
            "marine_warning",
        }:
            alert_score = {
                "flood_alert": 8,
                "coastal_flood_alert": 8,
                "rip_current_alert": 7,
                "high_surf_alert": 7,
                "thunderstorm_alert": 5,
                "marine_warning": 5,
                "weather_alert": 3,
            }.get(str(signal_type), 3)
            inputs["weather_alert_score"] = max(float(inputs["weather_alert_score"]), alert_score)
            inputs["weather_alerts"].append(
                {
                    "visibility": "public",
                    "signal_type": signal_type,
                    "headline": signal.get("headline"),
                    "timestamp": signal.get("timestamp"),
                    "expires_at": signal.get("expires_at"),
                    "confidence": signal.get("confidence"),
                }
            )

        if status == "stale":
            inputs["provider_status"][f"signal:{signal_type}"] = "stale"
        elif relevance and relevance >= 0.7:
            inputs["provider_status"][f"signal:{signal_type}"] = "ok"

    return inputs


def data_freshness_summary(signals: list[dict[str, Any]], expected_sources: list[str] | None = None) -> dict[str, Any]:
    summary = {source: {"status": "missing"} for source in expected_sources or []}
    for signal in active_public_signals(signals):
        provider = signal.get("source", {}).get("provider", signal.get("signal_type", "unknown"))
        summary[provider] = signal.get("data_freshness", {"status": "unknown"})
    return summary
