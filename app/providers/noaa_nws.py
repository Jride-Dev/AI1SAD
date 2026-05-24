from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.mongodb import COLLECTIONS
from app.providers.base import ProviderSignal, ProviderUnavailable, utc_now
from app.services.signal_broker import normalize_provider_signal


NOAA_NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
NOAA_NWS_CACHE_SECONDS = 300
NOAA_USER_AGENT = "AI1SAD/0.1 (research prototype; contact: https://github.com/Jride-Dev/AI1SAD)"
_CACHE: dict[tuple[float, float], tuple[datetime, dict[str, Any]]] = {}


ALERT_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...], float, list[str]]] = [
    ("rip_current_alert", ("rip current",), 0.75, ["rip_current", "surf_hazard"]),
    ("high_surf_alert", ("high surf", "surf advisory"), 0.7, ["high_surf", "surf_hazard"]),
    ("coastal_flood_alert", ("coastal flood",), 0.75, ["coastal_flood", "runoff"]),
    ("flood_alert", ("flood", "flash flood"), 0.8, ["flooding", "runoff"]),
    ("thunderstorm_alert", ("thunderstorm",), 0.65, ["thunderstorm", "weather_hazard"]),
    ("marine_warning", ("marine", "small craft", "gale", "storm warning", "hazardous seas"), 0.65, ["marine_weather"]),
]


def is_us_supported_coordinate(lat: float, lon: float) -> bool:
    return 18 <= lat <= 72 and -180 <= lon <= -60


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def classify_event(event: str, headline: str | None = None) -> tuple[str, float, list[str]]:
    text = f"{event} {headline or ''}".lower()
    for signal_type, keywords, relevance, factors in ALERT_TYPE_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return signal_type, relevance, factors
    return "weather_alert", 0.45, ["weather_alert"]


def _safe_summary(text: str | None) -> str:
    value = (text or "").replace("\r", " ").replace("\n", " ").strip()
    return value[:240]


class NoaaNwsProvider:
    provider_name = "noaa_nws"
    dataset = "nws_active_alerts"

    def __init__(self, *, timeout: int = 10, cache_seconds: int = NOAA_NWS_CACHE_SECONDS) -> None:
        self.timeout = timeout
        self.cache_seconds = cache_seconds

    def fetch_active_alerts(self, *, lat: float, lon: float) -> dict[str, Any]:
        if not is_us_supported_coordinate(lat, lon):
            return {
                "provider": self.provider_name,
                "status": "not_applicable",
                "alerts": [],
                "observed_at": utc_now(),
                "source_url": None,
                "cached": False,
            }

        now = utc_now()
        key = (round(float(lat), 4), round(float(lon), 4))
        cached = _CACHE.get(key)
        if cached and (now - cached[0]).total_seconds() < self.cache_seconds:
            result = dict(cached[1])
            result["cached"] = True
            return result

        params = urlencode({"point": f"{lat},{lon}"})
        url = f"{NOAA_NWS_ALERTS_URL}?{params}"
        request = Request(url, headers={"User-Agent": NOAA_USER_AGENT, "Accept": "application/geo+json, application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderUnavailable(f"NOAA/NWS request failed: {type(exc).__name__}") from exc

        features = payload.get("features", [])
        alerts = []
        for feature in features:
            props = feature.get("properties", {})
            event = str(props.get("event") or "Weather Alert")
            signal_type, relevance, factors = classify_event(event, props.get("headline"))
            effective = _parse_dt(props.get("effective")) or _parse_dt(props.get("sent")) or now
            expires = _parse_dt(props.get("expires")) or _parse_dt(props.get("ends")) or now + timedelta(hours=6)
            alerts.append(
                {
                    "id": props.get("id") or feature.get("id"),
                    "event": event,
                    "headline": _safe_summary(props.get("headline")),
                    "severity": props.get("severity"),
                    "certainty": props.get("certainty"),
                    "urgency": props.get("urgency"),
                    "effective": effective,
                    "expires": expires,
                    "signal_type": signal_type,
                    "relevance_score": relevance,
                    "risk_factors": factors,
                }
            )

        result = {
            "provider": self.provider_name,
            "status": "ok",
            "alerts": alerts,
            "observed_at": now,
            "source_url": url,
            "cached": False,
        }
        _CACHE[key] = (now, result)
        return dict(result)

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[ProviderSignal]:
        response = self.fetch_active_alerts(lat=lat, lon=lon)
        if response["status"] == "not_applicable":
            return []
        location = {"geo": {"type": "Point", "coordinates": [lon, lat]}}
        signals: list[ProviderSignal] = []
        for alert in response["alerts"]:
            signals.append(
                ProviderSignal(
                    signal_type=alert["signal_type"],
                    timestamp=alert["effective"],
                    expires_at=alert["expires"],
                    location=location,
                    provider=self.provider_name,
                    confidence=0.75,
                    value=1,
                    units="alert",
                    dataset=self.dataset,
                    risk_factors=alert["risk_factors"],
                    relevance_score=alert["relevance_score"],
                )
            )
        return signals

    def fetch_normalized_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[dict[str, Any]]:
        response = self.fetch_active_alerts(lat=lat, lon=lon)
        if response["status"] == "not_applicable":
            return []
        raw_signals = self.fetch_signals(lat=lat, lon=lon, radius_km=radius_km, lookback_hours=lookback_hours)
        normalized = [normalize_provider_signal(signal) for signal in raw_signals]
        for signal, alert in zip(normalized, response["alerts"]):
            signal["provider_timestamp"] = response["observed_at"]
            signal["alert_event"] = alert["event"]
            signal["headline"] = alert["headline"]
            signal["severity"] = alert.get("severity")
            signal["certainty"] = alert.get("certainty")
            signal["urgency"] = alert.get("urgency")
        return normalized


def fetch_live_noaa_nws_signals(*, lat: float, lon: float, lookback_hours: int = 72, timeout: int = 10) -> list[dict[str, Any]]:
    return NoaaNwsProvider(timeout=timeout).fetch_normalized_signals(lat=lat, lon=lon, lookback_hours=lookback_hours)


def noaa_nws_status_for_location(lat: float, lon: float) -> str:
    return "ok" if is_us_supported_coordinate(lat, lon) else "not_applicable"


def record_provider_success(db: Any, *, records_ingested: int, observed_at: datetime | None = None, status: str = "healthy") -> None:
    now = utc_now()
    run = {
        "provider": "noaa_nws",
        "status": "success" if status != "not_applicable" else "not_applicable",
        "started_at": now,
        "completed_at": now,
        "records_ingested": records_ingested,
    }
    health = {
        "_id": "noaa_nws",
        "provider": "noaa_nws",
        "last_success": observed_at or now if status != "not_applicable" else None,
        "last_error": None,
        "records_ingested": records_ingested,
        "status": status,
    }
    try:
        db[COLLECTIONS["provider_runs"]].insert_one(run)
        db[COLLECTIONS["provider_health"]].replace_one({"_id": "noaa_nws"}, health, upsert=True)
    except Exception:
        return


def record_provider_failure(db: Any, *, error: Exception) -> None:
    now = utc_now()
    summary = f"{type(error).__name__}: {str(error)[:160]}"
    existing_health = None
    try:
        existing_health = db[COLLECTIONS["provider_health"]].find_one({"_id": "noaa_nws"})
    except Exception:
        existing_health = None
    failure = {
        "provider": "noaa_nws",
        "failed_at": now,
        "status": "failed",
        "error_type": type(error).__name__,
        "error_summary": summary,
    }
    health = {
        "_id": "noaa_nws",
        "provider": "noaa_nws",
        "last_success": (existing_health or {}).get("last_success"),
        "last_error": summary,
        "records_ingested": 0,
        "status": "degraded",
    }
    try:
        db[COLLECTIONS["provider_failures"]].insert_one(failure)
        db[COLLECTIONS["provider_health"]].replace_one({"_id": "noaa_nws"}, health, upsert=True)
    except Exception:
        return
