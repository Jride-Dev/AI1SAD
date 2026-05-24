from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.disclaimers import AI1SAD_API_DISCLAIMER
from app.replay.quiet_day import QuietDayBaseline
from app.services.warning_engine import parse_dt


ALERT_TYPES = {
    "general_warning",
    "surveillance_priority",
    "activity_hazard",
    "biological_event",
    "sighting_cluster",
    "post_incident_surveillance",
}

ALERT_LEVELS = {"advisory", "watch", "warning", "urgent_surveillance"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _level_for(score: float, *, urgent_threshold: float = 85) -> str:
    if score >= urgent_threshold:
        return "urgent_surveillance"
    if score >= 70:
        return "warning"
    if score >= 45:
        return "watch"
    return "advisory"


def _expires(hours: int, reason: str, now: datetime) -> dict[str, Any]:
    return {"created_at": now, "expires_at": now + timedelta(hours=hours), "reason": reason}


def _zone(payload: dict[str, Any]) -> dict[str, Any]:
    lat = float(payload.get("lat", payload.get("location", {}).get("lat", 0)))
    lon = float(payload.get("lon", payload.get("location", {}).get("lon", 0)))
    return {
        "zone_id": payload.get("zone_id"),
        "location": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
        "radius_km": payload.get("radius_km", 2.5),
        "polygon": payload.get("polygon"),
    }


def _dominant(payload: dict[str, Any]) -> list[dict[str, Any]]:
    factors = payload.get("dominant_factors") or payload.get("activity_hazard_factors") or []
    safe = []
    for factor in factors[:6]:
        item = dict(factor)
        item.pop("private_notes", None)
        item.pop("restricted", None)
        safe.append(item)
    return safe


def _freshness(payload: dict[str, Any]) -> dict[str, Any]:
    freshness = dict(payload.get("data_freshness") or {})
    for value in freshness.values():
        if isinstance(value, dict):
            value.pop("private_notes", None)
            value.pop("restricted", None)
    return freshness


def _has_stale_or_expired_only(payload: dict[str, Any]) -> bool:
    freshness = _freshness(payload)
    if not freshness:
        return False
    statuses = {str(value.get("status", "")).lower() for value in freshness.values() if isinstance(value, dict)}
    return bool(statuses) and statuses <= {"stale", "expired"}


def _public_recent_signals(payload: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    signals = []
    for signal in payload.get("signals", []):
        if signal.get("visibility", "public") != "public":
            continue
        expires_at = parse_dt(signal.get("expires_at"))
        if expires_at and expires_at < now:
            continue
        item = dict(signal)
        item.pop("private_notes", None)
        item.pop("restricted", None)
        signals.append(item)
    return signals


def _base_alert(
    payload: dict[str, Any],
    *,
    alert_type: str,
    level: str,
    title: str,
    summary: str,
    recommended_action: str,
    trigger: dict[str, Any],
    expires_hours: int,
    now: datetime,
    confidence: float,
) -> dict[str, Any]:
    zone = _zone(payload)
    return {
        "visibility": "public",
        "status": "active",
        "alert_type": alert_type,
        "level": level,
        "title": title,
        "summary": summary,
        "zone": zone,
        "location": zone["location"],
        "recommended_action": recommended_action,
        "dominant_factors": _dominant(payload),
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "data_freshness": _freshness(payload),
        "trigger": trigger,
        "audience": {"audiences": payload.get("audiences", ["drone_operators", "lifeguards", "beach_managers", "api_users"])},
        "delivery_status": {"status": "not_sent", "channels": []},
        "expiration": _expires(expires_hours, "time-limited operational alert", now),
        "expires_at": now + timedelta(hours=expires_hours),
        "disclaimer": AI1SAD_API_DISCLAIMER,
    }


def evaluate_alerts(payload: dict[str, Any], *, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or _now()
    if payload.get("visibility", "public") not in {"public", None}:
        return []
    if _has_stale_or_expired_only(payload):
        return []

    warning_score = float(payload.get("warning_score", 0) or 0)
    surveillance_score = float(payload.get("surveillance_priority_score", payload.get("priority_score", 0)) or 0)
    activity_score = float(payload.get("activity_hazard_score", payload.get("activity_context_score", 0)) or 0)
    confidence = float(payload.get("confidence", 0.5) or 0.5)
    quiet_delta = float(payload.get("quiet_day_comparison", {}).get("delta", payload.get("quiet_day_delta", 0)) or 0)
    signals = _public_recent_signals(payload, now)
    alerts: list[dict[str, Any]] = []

    weak_scores = max(warning_score, surveillance_score, activity_score) < 45
    if weak_scores and quiet_delta <= 10 and not signals:
        return []

    if surveillance_score >= 75:
        alerts.append(
            _base_alert(
                payload,
                alert_type="surveillance_priority",
                level=_level_for(surveillance_score),
                title="High surveillance-priority zone",
                summary="Safety teams should prioritize this area for drone, lookout, or patrol review even if the general warning score is low.",
                recommended_action="Prioritize drone/search coverage for this zone and review local safety guidance before water activity.",
                trigger={"trigger_type": "surveillance_priority_score", "threshold": 75, "observed_value": surveillance_score, "rationale": "High surveillance priority can create an alert even when general warning is low."},
                expires_hours=6,
                now=now,
                confidence=confidence,
            )
        )

    if activity_score >= 45:
        alerts.append(
            _base_alert(
                payload,
                alert_type="activity_hazard",
                level=_level_for(activity_score, urgent_threshold=90),
                title="Activity-specific shark encounter hazard",
                summary="The selected activity context increases encounter hazard in this area.",
                recommended_action="Issue activity-specific caution and consider targeted safety messaging for the relevant water activity.",
                trigger={"trigger_type": "activity_hazard_score", "threshold": 45, "observed_value": activity_score, "rationale": "Activity hazard creates activity-specific alerts."},
                expires_hours=4,
                now=now,
                confidence=confidence,
            )
        )

    if warning_score >= 70 and quiet_delta > 10:
        alerts.append(
            _base_alert(
                payload,
                alert_type="general_warning",
                level=_level_for(warning_score),
                title="Elevated environmental warning conditions",
                summary="Environmental/live-condition signals are elevated above quiet-day baseline.",
                recommended_action="Review beach, lifeguard, weather, and wildlife guidance before operations or water activity.",
                trigger={"trigger_type": "warning_score", "threshold": 70, "observed_value": warning_score, "rationale": "General warning is elevated and not suppressed by quiet-day baseline."},
                expires_hours=6,
                now=now,
                confidence=confidence,
            )
        )

    sighting_count = sum(1 for signal in signals if signal.get("signal_type") in {"sighting", "shark_sighting"})
    carcass_count = sum(1 for signal in signals if signal.get("signal_type") in {"carcass", "whale_carcass", "biological_event"})
    recent_interactions = int(payload.get("recent_interactions_count", 0) or 0)

    if sighting_count >= 2:
        alerts.append(
            _base_alert(
                payload,
                alert_type="sighting_cluster",
                level="watch",
                title="Recent shark sighting cluster",
                summary="Multiple recent public sighting signals are active near this location.",
                recommended_action="Increase visual monitoring and verify reports with local authorities.",
                trigger={"trigger_type": "sighting_cluster", "threshold": 2, "observed_value": sighting_count},
                expires_hours=3,
                now=now,
                confidence=max(confidence - 0.05, 0.25),
            )
        )

    if carcass_count:
        alerts.append(
            _base_alert(
                payload,
                alert_type="biological_event",
                level="advisory",
                title="Biological event advisory",
                summary="A carcass, prey, or biological event signal is active near this location.",
                recommended_action="Review wildlife authority guidance and consider temporary targeted monitoring.",
                trigger={"trigger_type": "biological_event", "threshold": 1, "observed_value": carcass_count},
                expires_hours=12,
                now=now,
                confidence=max(confidence - 0.05, 0.25),
            )
        )

    if recent_interactions:
        alerts.append(
            _base_alert(
                payload,
                alert_type="post_incident_surveillance",
                level="urgent_surveillance",
                title="Post-incident surveillance priority",
                summary="A recent interaction context supports time-limited post-incident surveillance.",
                recommended_action="Prioritize drone/search coverage and coordinate with official response teams.",
                trigger={"trigger_type": "recent_interaction", "threshold": 1, "observed_value": recent_interactions},
                expires_hours=12,
                now=now,
                confidence=confidence,
            )
        )

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for alert in alerts:
        unique[(alert["alert_type"], alert["level"])] = alert
    return list(unique.values())


def alert_examples() -> dict[str, dict[str, Any]]:
    return {
        "horseshoe_reef": {
            "lat": -31.9826564,
            "lon": 115.5153234,
            "warning_score": 0,
            "activity_hazard_score": 58,
            "surveillance_priority_score": 99.3,
            "confidence": 0.48,
            "dominant_factors": [{"factor": "WA reef spearfishing white shark context", "points": 58}],
            "data_freshness": {"environmental": {"status": "missing"}},
        },
        "florida_inlet_rainfall": {
            "lat": 27.7,
            "lon": -80.2,
            "warning_score": 76,
            "activity_hazard_score": 22,
            "surveillance_priority_score": 68,
            "quiet_day_delta": 40,
            "confidence": 0.72,
            "dominant_factors": [{"factor": "rainfall_runoff_inlet", "points": 30}],
        },
        "hawaii_october_tiger": {
            "lat": 21.3,
            "lon": -157.8,
            "warning_score": 48,
            "activity_hazard_score": 30,
            "surveillance_priority_score": 62,
            "confidence": 0.65,
            "dominant_factors": [{"factor": "hawaii_october_tiger_context", "points": 20}],
        },
        "red_sea_carcass_shipping": {
            "lat": 20.5,
            "lon": 38.5,
            "warning_score": 55,
            "activity_hazard_score": 10,
            "surveillance_priority_score": 58,
            "confidence": 0.6,
            "signals": [{"visibility": "public", "signal_type": "carcass", "expires_at": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()}],
            "dominant_factors": [{"factor": "carcass_shipping_anomaly", "points": 18}],
        },
    }
