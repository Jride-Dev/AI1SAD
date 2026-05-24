from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.providers.base import ProviderSignal, utc_now
from app.services.signal_broker import normalize_provider_signal


class NoaaCoastwatchProvider:
    provider_name = "noaa_coastwatch"
    dataset = "offline_sst_adapter"

    def __init__(self, *, offline_records: list[dict[str, Any]] | None = None) -> None:
        self.offline_records = offline_records or []

    def fetch_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[ProviderSignal]:
        signals: list[ProviderSignal] = []
        for record in self.offline_records:
            timestamp = _parse_timestamp(record.get("timestamp") or record.get("observed_at")) or utc_now()
            expires_at = _parse_timestamp(record.get("expires_at")) or timestamp + timedelta(hours=48)
            rec_lat = float(record.get("lat", lat))
            rec_lon = float(record.get("lon", lon))
            location = {"geo": {"type": "Point", "coordinates": [rec_lon, rec_lat]}}
            temperature = record.get("temperature_c", record.get("sea_surface_temp_c"))
            anomaly = record.get("anomaly_c", record.get("sst_anomaly_c"))
            confidence = float(record.get("confidence", 0.7))
            if temperature is not None:
                signals.append(
                    ProviderSignal(
                        signal_type="sea_surface_temperature",
                        timestamp=timestamp,
                        expires_at=expires_at,
                        location=location,
                        provider=self.provider_name,
                        confidence=confidence,
                        value=float(temperature),
                        units="c",
                        dataset=str(record.get("dataset", self.dataset)),
                        risk_factors=["sst_species_suitability"],
                        relevance_score=0.55,
                    )
                )
            if anomaly is not None:
                signals.append(
                    ProviderSignal(
                        signal_type="sst_anomaly",
                        timestamp=timestamp,
                        expires_at=expires_at,
                        location=location,
                        provider=self.provider_name,
                        confidence=max(0.45, confidence - 0.05),
                        value=float(anomaly),
                        units="c",
                        dataset=str(record.get("dataset", self.dataset)),
                        risk_factors=["sst_anomaly_context"],
                        relevance_score=0.5,
                    )
                )
            if temperature is not None or anomaly is not None:
                context_value = {
                    "temperature_c": float(temperature) if temperature is not None else None,
                    "anomaly_c": float(anomaly) if anomaly is not None else None,
                }
                signals.append(
                    ProviderSignal(
                        signal_type="ocean_temperature_context",
                        timestamp=timestamp,
                        expires_at=expires_at,
                        location=location,
                        provider=self.provider_name,
                        confidence=confidence,
                        value=context_value,
                        units="context",
                        dataset=str(record.get("dataset", self.dataset)),
                        risk_factors=["regional_sst_context"],
                        relevance_score=0.45,
                    )
                )
        return signals

    def fetch_normalized_signals(self, *, lat: float, lon: float, radius_km: float = 0, lookback_hours: int = 72) -> list[dict[str, Any]]:
        normalized = [normalize_provider_signal(signal) for signal in self.fetch_signals(lat=lat, lon=lon, radius_km=radius_km, lookback_hours=lookback_hours)]
        temperature_c = next((signal.get("value") for signal in normalized if signal.get("signal_type") == "sea_surface_temperature"), None)
        anomaly_c = next((signal.get("value") for signal in normalized if signal.get("signal_type") == "sst_anomaly"), None)
        for signal in normalized:
            if signal.get("signal_type") == "ocean_temperature_context" and isinstance(signal.get("value"), dict):
                temperature_c = signal["value"].get("temperature_c", temperature_c)
                anomaly_c = signal["value"].get("anomaly_c", anomaly_c)
        for signal in normalized:
            signal["provider_timestamp"] = signal["timestamp"]
            signal["temperature_c"] = temperature_c
            signal["anomaly_c"] = anomaly_c
        return normalized


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


def normalize_offline_sst_records(records: list[dict[str, Any]], *, lat: float, lon: float) -> list[dict[str, Any]]:
    return NoaaCoastwatchProvider(offline_records=records).fetch_normalized_signals(lat=lat, lon=lon)
