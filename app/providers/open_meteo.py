from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.mongodb import COLLECTIONS
from app.providers.base import ProviderSignal, ProviderUnavailable, utc_now
from app.services.signal_broker import normalize_provider_signal


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_CACHE_SECONDS = 600
_CACHE: dict[tuple[float, float, int], tuple[datetime, dict[str, Any]]] = {}


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _recent_values(times: list[Any], values: list[Any], lookback_hours: int, now: datetime) -> list[float]:
    cutoff = now - timedelta(hours=lookback_hours)
    paired: list[float] = []
    if times and len(times) == len(values):
        for text, value in zip(times, values):
            timestamp = _parse_time(text)
            if timestamp and cutoff <= timestamp <= now and value is not None:
                paired.append(float(value))
    else:
        paired = [float(value) for value in values[-lookback_hours:] if value is not None]
    return paired


def _latest_value(times: list[Any], values: list[Any], now: datetime) -> float | None:
    if times and len(times) == len(values):
        for text, value in reversed(list(zip(times, values))):
            timestamp = _parse_time(text)
            if timestamp and timestamp <= now and value is not None:
                return float(value)
    for value in reversed(values):
        if value is not None:
            return float(value)
    return None


def _sum_last(values: list[float], hours: int) -> float:
    return round(sum(values[-hours:]), 2)


class OpenMeteoProvider:
    provider_name = "open_meteo"
    dataset = "open_meteo_forecast_hourly"

    def __init__(self, *, timeout: int = 10, cache_seconds: int = OPEN_METEO_CACHE_SECONDS) -> None:
        self.timeout = timeout
        self.cache_seconds = cache_seconds

    def fetch_recent_weather(self, *, lat: float, lon: float, lookback_hours: int = 72) -> dict[str, Any]:
        now = utc_now()
        key = (round(float(lat), 4), round(float(lon), 4), int(lookback_hours))
        cached = _CACHE.get(key)
        if cached and (now - cached[0]).total_seconds() < self.cache_seconds:
            result = dict(cached[1])
            result["cached"] = True
            return result

        past_days = max(1, min(14, ceil(lookback_hours / 24)))
        params = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "hourly": "rain,temperature_2m,wind_speed_10m",
                "past_days": past_days,
                "forecast_days": 1,
                "timezone": "UTC",
            }
        )
        url = f"{OPEN_METEO_FORECAST_URL}?{params}"
        try:
            with urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderUnavailable(f"Open-Meteo request failed: {type(exc).__name__}") from exc

        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        rainfall_values = _recent_values(times, hourly.get("rain", []), lookback_hours, now)
        temp_latest = _latest_value(times, hourly.get("temperature_2m", []), now)
        wind_latest = _latest_value(times, hourly.get("wind_speed_10m", []), now)
        provider_timestamp = now
        for text in reversed(times):
            parsed = _parse_time(text)
            if parsed and parsed <= now:
                provider_timestamp = parsed
                break

        result = {
            "provider": self.provider_name,
            "status": "ok",
            "observed_at": provider_timestamp,
            "received_at": now,
            "rainfall_24h_mm": _sum_last(rainfall_values, 24),
            "rainfall_48h_mm": _sum_last(rainfall_values, 48),
            "rainfall_72h_mm": _sum_last(rainfall_values, 72),
            "temperature_c": temp_latest,
            "wind_speed_kmh": wind_latest,
            "source_url": url,
            "cached": False,
        }
        _CACHE[key] = (now, result)
        return dict(result)

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[ProviderSignal]:
        weather = self.fetch_recent_weather(lat=lat, lon=lon, lookback_hours=lookback_hours)
        timestamp = weather["observed_at"]
        location = {"geo": {"type": "Point", "coordinates": [lon, lat]}}
        signals = [
            ProviderSignal(
                signal_type="weather_rainfall",
                timestamp=timestamp,
                location=location,
                provider=self.provider_name,
                confidence=0.85,
                value=weather["rainfall_72h_mm"],
                units="mm",
                dataset=self.dataset,
                risk_factors=["rainfall_runoff"],
                relevance_score=0.8,
            )
        ]
        if weather.get("temperature_c") is not None:
            signals.append(
                ProviderSignal(
                    signal_type="weather_temperature",
                    timestamp=timestamp,
                    location=location,
                    provider=self.provider_name,
                    confidence=0.75,
                    value=weather["temperature_c"],
                    units="c",
                    dataset=self.dataset,
                    risk_factors=["weather_context"],
                    relevance_score=0.35,
                )
            )
        if weather.get("wind_speed_kmh") is not None:
            signals.append(
                ProviderSignal(
                    signal_type="weather_wind_speed",
                    timestamp=timestamp,
                    location=location,
                    provider=self.provider_name,
                    confidence=0.65,
                    value=weather["wind_speed_kmh"],
                    units="kmh",
                    dataset=self.dataset,
                    risk_factors=["weather_context"],
                    relevance_score=0.25,
                )
            )
        return signals

    def fetch_normalized_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(lat=lat, lon=lon, radius_km=radius_km, lookback_hours=lookback_hours)]
        weather = self.fetch_recent_weather(lat=lat, lon=lon, lookback_hours=lookback_hours)
        for signal in normalized:
            if signal.get("signal_type") == "weather_rainfall":
                signal["rainfall_24h_mm"] = weather["rainfall_24h_mm"]
                signal["rainfall_48h_mm"] = weather["rainfall_48h_mm"]
                signal["rainfall_72h_mm"] = weather["rainfall_72h_mm"]
            if signal.get("signal_type") == "weather_temperature":
                signal["temperature_c"] = weather["temperature_c"]
            if signal.get("signal_type") == "weather_wind_speed":
                signal["wind_speed_kmh"] = weather["wind_speed_kmh"]
            signal["provider_timestamp"] = weather["observed_at"]
        return normalized


def fetch_previous_72h(lat: float, lon: float, timeout: int = 10) -> dict[str, Any]:
    return OpenMeteoProvider(timeout=timeout).fetch_recent_weather(lat=lat, lon=lon, lookback_hours=72)


def fetch_live_open_meteo_signals(*, lat: float, lon: float, lookback_hours: int = 72, timeout: int = 10) -> list[dict[str, Any]]:
    return OpenMeteoProvider(timeout=timeout).fetch_normalized_signals(lat=lat, lon=lon, lookback_hours=lookback_hours)


def record_provider_success(db: Any, *, records_ingested: int, observed_at: datetime | None = None) -> None:
    now = utc_now()
    run = {
        "provider": "open_meteo",
        "status": "success",
        "started_at": now,
        "completed_at": now,
        "records_ingested": records_ingested,
    }
    health = {
        "_id": "open_meteo",
        "provider": "open_meteo",
        "last_success": observed_at or now,
        "last_error": None,
        "records_ingested": records_ingested,
        "status": "healthy",
    }
    try:
        db[COLLECTIONS["provider_runs"]].insert_one(run)
        db[COLLECTIONS["provider_health"]].replace_one({"_id": "open_meteo"}, health, upsert=True)
    except Exception:
        return


def record_provider_failure(db: Any, *, error: Exception) -> None:
    now = utc_now()
    summary = f"{type(error).__name__}: {str(error)[:160]}"
    existing_health = None
    try:
        existing_health = db[COLLECTIONS["provider_health"]].find_one({"_id": "open_meteo"})
    except Exception:
        existing_health = None
    failure = {
        "provider": "open_meteo",
        "failed_at": now,
        "status": "failed",
        "error_type": type(error).__name__,
        "error_summary": summary,
    }
    health = {
        "_id": "open_meteo",
        "provider": "open_meteo",
        "last_success": (existing_health or {}).get("last_success"),
        "last_error": summary,
        "records_ingested": 0,
        "status": "degraded",
    }
    try:
        db[COLLECTIONS["provider_failures"]].insert_one(failure)
        db[COLLECTIONS["provider_health"]].replace_one({"_id": "open_meteo"}, health, upsert=True)
    except Exception:
        return
