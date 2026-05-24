from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class SignalDecayModel:
    def __init__(self, half_life_hours: float = 24.0, expiry_multiplier: float = 3.0):
        self.half_life_hours = half_life_hours
        self.expiry_multiplier = expiry_multiplier

    def decay_weight(self, signal_age_hours: float) -> float:
        if signal_age_hours <= 0:
            return 1.0
        if signal_age_hours >= self.half_life_hours * self.expiry_multiplier:
            return 0.0
        return 2.0 ** (-signal_age_hours / self.half_life_hours)

    def weight_from_timestamp(self, timestamp: datetime, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        age_hours = (now - ts).total_seconds() / 3600
        return self.decay_weight(age_hours)

    def effective_value(self, raw_value: float, signal_age_hours: float) -> float:
        return round(raw_value * self.decay_weight(signal_age_hours), 4)

    def factor_decay_contribution(self, points: float, signal_age_hours: float) -> float:
        return round(points * self.decay_weight(signal_age_hours), 4)


SIGNAL_TYPE_DECAY_PARAMS: dict[str, dict[str, float]] = {
    "sighting": {"half_life_hours": 12.0, "expiry_multiplier": 3.0},
    "shark_sighting": {"half_life_hours": 12.0, "expiry_multiplier": 3.0},
    "weather_rainfall": {"half_life_hours": 6.0, "expiry_multiplier": 4.0},
    "rainfall": {"half_life_hours": 6.0, "expiry_multiplier": 4.0},
    "ocean_sst": {"half_life_hours": 24.0, "expiry_multiplier": 3.0},
    "sst": {"half_life_hours": 24.0, "expiry_multiplier": 3.0},
    "sst_anomaly": {"half_life_hours": 48.0, "expiry_multiplier": 2.5},
    "vessel_activity": {"half_life_hours": 12.0, "expiry_multiplier": 3.0},
    "fishing_activity": {"half_life_hours": 12.0, "expiry_multiplier": 3.0},
    "biological_event": {"half_life_hours": 72.0, "expiry_multiplier": 2.0},
    "carcass": {"half_life_hours": 72.0, "expiry_multiplier": 2.0},
    "whale_carcass": {"half_life_hours": 72.0, "expiry_multiplier": 2.0},
    "human_exposure": {"half_life_hours": 24.0, "expiry_multiplier": 3.0},
}


def decay_model_for(signal_type: str) -> SignalDecayModel:
    params = SIGNAL_TYPE_DECAY_PARAMS.get(signal_type, {"half_life_hours": 24.0, "expiry_multiplier": 3.0})
    return SignalDecayModel(half_life_hours=params["half_life_hours"], expiry_multiplier=params["expiry_multiplier"])


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def apply_decay_to_signals(signals: list[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    decayed: list[dict[str, Any]] = []
    for signal in signals:
        signal_type = signal.get("signal_type", "unknown")
        model = decay_model_for(signal_type)
        raw_ts = signal.get("timestamp") or signal.get("observed_at")
        timestamp = _parse_ts(raw_ts)
        if not timestamp:
            decayed.append(signal)
            continue
        ts = timestamp
        age_hours = (now - ts).total_seconds() / 3600
        weight = model.decay_weight(age_hours)
        decayed_signal = dict(signal)
        decayed_signal["decay_weight"] = round(weight, 4)
        decayed_signal["age_hours"] = round(age_hours, 2)
        value = signal.get("value")
        if value is not None:
            try:
                decayed_signal["decayed_value"] = model.effective_value(float(value), age_hours)
            except (ValueError, TypeError):
                decayed_signal["decayed_value"] = None
        decayed_signal["decay_model"] = {
            "half_life_hours": model.half_life_hours,
            "expiry_multiplier": model.expiry_multiplier,
            "expires_after_hours": model.half_life_hours * model.expiry_multiplier,
        }
        if weight > 0:
            decayed.append(decayed_signal)
    return decayed
