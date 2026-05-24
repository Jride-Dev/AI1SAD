from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.disclaimers import AI1SAD_API_DISCLAIMER
from app.risk_model import RISK_DISCLAIMER, band_for_score, nearest_profile, profile_summary
from app.services.activity_hazard import activity_hazard_score


WARNING_DISCLAIMER = AI1SAD_API_DISCLAIMER


def clamp(value: float, low: float = 0, high: float = 1) -> float:
    return max(low, min(high, value))


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def rainfall_intensity_score(rainfall_72h_mm: float) -> float:
    if rainfall_72h_mm >= 100:
        return 20
    if rainfall_72h_mm >= 50:
        return 15
    if rainfall_72h_mm >= 25:
        return 10
    if rainfall_72h_mm >= 10:
        return 5
    return 0


def river_mouth_proximity_score(distance_km: float | None) -> float:
    if distance_km is None:
        return 0
    if distance_km <= 1:
        return 15
    if distance_km <= 5:
        return 10
    if distance_km <= 10:
        return 5
    return 0


def biological_event_score(events: list[dict[str, Any]], now: datetime | None = None, max_age_days: int = 14) -> float:
    now = now or datetime.now(timezone.utc)
    score = 0.0
    for event in events:
        if event.get("visibility", "public") != "public":
            continue
        observed_at = parse_dt(event.get("observed_at"))
        expires_at = parse_dt(event.get("expires_at"))
        if expires_at and expires_at < now:
            continue
        if observed_at and observed_at < now - timedelta(days=max_age_days):
            continue
        event_type = str(event.get("event_type", "")).lower()
        if "whale" in event_type and "carcass" in event_type:
            score = max(score, 20)
        elif "stranding" in event_type or "carcass" in event_type:
            score = max(score, 12)
        elif "baitfish" in event_type or "prey" in event_type:
            score = max(score, 8)
    return score


def is_stale(document: dict[str, Any], now: datetime, lookback_hours: int) -> bool:
    observed_at = parse_dt(document.get("observed_at"))
    if not observed_at:
        return True
    return observed_at < now - timedelta(hours=lookback_hours)


def regional_seasonal_multiplier(profile: dict[str, Any] | None, month: int | None) -> tuple[float, list[dict[str, Any]]]:
    if not profile or not month:
        return 1.0, []
    multipliers = profile.get("environmental_multipliers", {})
    applied: list[dict[str, Any]] = []
    multiplier = 1.0
    if month in profile.get("local_summer_high_exposure_months", []):
        value = multipliers.get("summer", 1.0)
        multiplier *= value
        applied.append({"factor": "regional_summer_high_exposure", "value": month, "multiplier": value})
    if month in profile.get("known_high_attention_months", []):
        value = multipliers.get("high_attention", 1.0)
        multiplier *= value
        applied.append({"factor": "regional_high_attention_month", "value": month, "multiplier": value})
    if profile.get("region_key") == "hawaii" and month == 10:
        value = multipliers.get("sharktober", 1.0)
        multiplier *= value
        applied.append({"factor": "hawaii_sharktober", "value": month, "multiplier": value})
    if profile.get("region_key") in {"new_south_wales_australia", "western_australia"} and month in {1, 2}:
        value = multipliers.get("australia_jan_feb", 1.0)
        multiplier *= value
        applied.append({"factor": "australia_jan_feb_high_exposure", "value": month, "multiplier": value})
    return round(multiplier, 4), applied


def calculate_warning(
    *,
    lat: float,
    lon: float,
    lookback_hours: int = 72,
    rainfall_72h_mm: float | None = None,
    river_mouth_distance_km: float | None = None,
    sea_surface_temp_c: float | None = None,
    sst_anomaly_c: float | None = None,
    vessel_activity_index: float | None = None,
    biological_events: list[dict[str, Any]] | None = None,
    weather_alerts: list[dict[str, Any]] | None = None,
    weather_alert_score: float | None = None,
    human_exposure_index: float | None = None,
    activity_context: str | None = None,
    reef_habitat: bool = False,
    dropoff_habitat: bool = False,
    bait_activity: bool = False,
    suspected_species: str | None = None,
    month: int | None = None,
    profiles: list[dict[str, Any]] | None = None,
    provider_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    profile = nearest_profile(lat, lon, profiles) if profiles is not None else None
    factors: list[dict[str, Any]] = []
    data_sources_used: list[str] = []
    missing_sources: set[str] = set()
    provider_status = provider_status or {}
    activity_hazard = activity_hazard_score(
        activity_context=activity_context,
        reef_habitat=reef_habitat,
        dropoff_habitat=dropoff_habitat,
        bait_activity=bait_activity,
        suspected_species=suspected_species,
        regional_profile=profile,
    )

    rainfall = rainfall_72h_mm or 0
    rain_score = rainfall_intensity_score(rainfall)
    factors.append({"factor": "rainfall_intensity_score", "value": rainfall, "points": rain_score, "rationale": "Rainfall in the previous 72 hours."})
    if rainfall_72h_mm is None:
        missing_sources.add("weather_observations")
    else:
        data_sources_used.append("weather_observations")

    runoff = min(15, round(rain_score * 0.5 + (5 if river_mouth_distance_km is not None and river_mouth_distance_km <= 5 else 0), 2))
    factors.append({"factor": "runoff_score", "value": rainfall, "points": runoff, "rationale": "Rainfall/runoff proxy near coastal water."})

    river_score = river_mouth_proximity_score(river_mouth_distance_km)
    factors.append({"factor": "river_mouth_proximity_score", "value": river_mouth_distance_km, "points": river_score, "rationale": "Nearest river mouth, inlet, estuary, or outflow."})

    if sea_surface_temp_c is None:
        sst_score = 0
        missing_sources.add("ocean_observations")
    elif 20 <= sea_surface_temp_c <= 28:
        sst_score = 10
        data_sources_used.append("ocean_observations")
    elif 15 <= sea_surface_temp_c < 20 or 28 < sea_surface_temp_c <= 31:
        sst_score = 5
        data_sources_used.append("ocean_observations")
    else:
        sst_score = 0
        data_sources_used.append("ocean_observations")
    factors.append({"factor": "sst_score", "value": sea_surface_temp_c, "points": sst_score, "rationale": "Sea-surface temperature suitability."})

    if sst_anomaly_c is None:
        anomaly_score = 0
        missing_sources.add("sst_anomaly")
    else:
        anomaly_score = min(8, abs(sst_anomaly_c) * 3)
        data_sources_used.append("sst_anomaly")
    factors.append({"factor": "sst_anomaly_score", "value": sst_anomaly_c, "points": round(anomaly_score, 2), "rationale": "Sea-surface temperature anomaly magnitude."})

    if vessel_activity_index is None:
        vessel_score = 0
        missing_sources.add("vessel_activity")
    else:
        vessel_score = round(clamp(vessel_activity_index) * 10, 2)
        data_sources_used.append("vessel_activity")
    factors.append({"factor": "fishing_vessel_activity_score", "value": vessel_activity_index, "points": vessel_score, "rationale": "Fishing or vessel activity signal."})

    bio_events = biological_events or []
    bio_score = biological_event_score(bio_events)
    if bio_events:
        data_sources_used.append("biological_events")
    else:
        missing_sources.add("biological_events")
    factors.append({"factor": "biological_event_score", "value": len(bio_events), "points": bio_score, "rationale": "Whale carcass, stranding, baitfish, or prey event signal."})

    alert_events = [event for event in weather_alerts or [] if event.get("visibility", "public") == "public"]
    alert_score = min(10, float(weather_alert_score or 0))
    if alert_events:
        data_sources_used.append("noaa_nws")
    factors.append({"factor": "weather_alert_score", "value": len(alert_events), "points": alert_score, "rationale": "NOAA/NWS public weather alert context such as flood, surf, rip current, thunderstorm, coastal flood, or marine warnings."})

    if human_exposure_index is None:
        human_score = 0
        missing_sources.add("human_exposure_estimates")
    else:
        human_score = round(clamp(human_exposure_index) * 12, 2)
        data_sources_used.append("human_exposure_estimates")
    factors.append({"factor": "human_exposure_score", "value": human_exposure_index, "points": human_score, "rationale": "Estimated number/intensity of people in the water."})

    base_score = sum(item["points"] for item in factors)
    multiplier, regional_factors = regional_seasonal_multiplier(profile, month)
    for regional_factor in regional_factors:
        factors.append({**regional_factor, "points": round(base_score * (regional_factor["multiplier"] - 1), 2), "rationale": "Regional seasonal multiplier."})
    warning_score = min(100, round(base_score * multiplier, 2))

    for provider, status in provider_status.items():
        if status == "ok":
            data_sources_used.append(provider)
        elif status == "stale":
            missing_sources.add(f"{provider}:stale")
        elif status == "not_applicable":
            continue
        else:
            missing_sources.add(provider)

    confidence = round(max(0.25, 0.9 - (0.07 * len(missing_sources))), 2)
    for factor in factors:
        factor["contribution"] = round((factor.get("points", 0) / warning_score), 4) if warning_score else 0
    dominant = sorted(factors, key=lambda item: item.get("points", 0), reverse=True)[:5]
    return {
        "location": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
        "warning_score": warning_score,
        "warning_band": band_for_score(warning_score),
        "activity_context_score": activity_hazard["activity_context_score"],
        "activity_context_band": activity_hazard["activity_context_band"],
        "activity_hazard_factors": activity_hazard["factors"],
        "confidence": confidence,
        "lookback_hours": lookback_hours,
        "signals": {
            "rainfall_72h_mm": rainfall_72h_mm,
            "rainfall_intensity_score": rain_score,
            "runoff_score": runoff,
            "river_mouth_proximity_score": river_score,
            "sst_score": sst_score,
            "sst_anomaly_score": round(anomaly_score, 2),
            "fishing_vessel_activity_score": vessel_score,
            "biological_event_score": bio_score,
            "weather_alert_score": alert_score,
            "human_exposure_score": human_score,
            "regional_seasonal_multiplier": multiplier,
        },
        "regional_profile": profile_summary(profile),
        "dominant_factors": dominant,
        "data_sources_used": sorted(set(data_sources_used)),
        "missing_data_sources": sorted(missing_sources),
        "score_split": {
            "warning_score": "Environmental/live-condition risk from weather, ocean, biological, vessel, and exposure signals.",
            "surveillance_priority_score": "Where safety or drone teams should look first.",
            "activity_hazard_score": "Risk introduced by what the human is doing in context. It is not attack probability.",
        },
        "disclaimer": WARNING_DISCLAIMER,
    }


def provider_health_document(provider: str, *, status: str, records_ingested: int = 0, last_success: str | None = None) -> dict[str, Any]:
    return {
        "_id": provider,
        "provider": provider,
        "last_success": last_success,
        "records_ingested": records_ingested,
        "status": status,
    }
