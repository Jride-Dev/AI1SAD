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
        confidence = float(event.get("confidence", 0.5) or 0.5)
        value = float(event.get("value", 1.0) or 1.0)
        confidence_factor = max(0.5, min(1.0, confidence))
        value_factor = max(0.5, min(1.0, value))
        if "whale" in event_type and "carcass" in event_type:
            score = max(score, round(24 * confidence_factor * value_factor, 2))
        elif "fish_kill" in event_type or ("fish" in event_type and "kill" in event_type):
            score = max(score, round(22 * confidence_factor * value_factor, 2))
        elif "stranding" in event_type or "carcass" in event_type:
            score = max(score, round(18 * confidence_factor * value_factor, 2))
        elif "baitfish" in event_type or "prey" in event_type:
            score = max(score, round(10 * confidence_factor * value_factor, 2))
        elif "seal" in event_type or "sea_lion" in event_type:
            score = max(score, round(7 * confidence_factor * value_factor, 2))
        elif "turtle" in event_type or "hatchling" in event_type or "migration" in event_type or "nesting" in event_type:
            score = max(score, round(5 * confidence_factor * value_factor, 2))
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


def regional_sst_context_score(profile: dict[str, Any] | None, sea_surface_temp_c: float | None, sst_anomaly_c: float | None) -> tuple[float, dict[str, Any] | None]:
    if not profile or sea_surface_temp_c is None:
        return 0, None
    region = profile.get("region_key")
    score = 0.0
    rationale = "Regional species-aware sea-surface temperature context."
    if region == "florida":
        if 24 <= sea_surface_temp_c <= 30:
            score = 4
            rationale = "Florida blacktip/bull context treats warm nearshore SST as suitable background context."
    elif region == "western_australia":
        if 17 <= sea_surface_temp_c <= 23:
            score = 4
            rationale = "Western Australia white shark context treats temperate SST as suitable background context."
    elif region == "hawaii":
        if 24 <= sea_surface_temp_c <= 29:
            score = 4
            rationale = "Hawaii tiger shark context treats warm tropical SST as suitable background context."
    elif region == "red_sea":
        if sea_surface_temp_c >= 27:
            score = 5
            rationale = "Red Sea warm-water context treats high SST as relevant background context."
    if sst_anomaly_c is not None:
        score += min(2, abs(float(sst_anomaly_c)))
    score = min(6, round(score, 2))
    if not score:
        return 0, None
    return score, {
        "factor": "regional_sst_species_context",
        "value": sea_surface_temp_c,
        "anomaly_c": sst_anomaly_c,
        "points": score,
        "rationale": rationale,
    }


def exposure_amplification_score(
    *,
    human_exposure_index: float | None,
    rain_score: float,
    runoff: float,
    sst_score: float,
    regional_sst_score: float,
    bio_score: float,
    alert_score: float,
    activity_context_score: float,
    profile: dict[str, Any] | None,
    month: int | None,
) -> tuple[float, dict[str, Any] | None]:
    if human_exposure_index is None or human_exposure_index < 0.55:
        return 0, None
    contexts = []
    if rain_score or runoff:
        contexts.append("rainfall_runoff")
    if sst_score or regional_sst_score:
        contexts.append("sst_suitability")
    if bio_score:
        contexts.append("biological_event")
    if alert_score:
        contexts.append("weather_alert")
    if activity_context_score >= 25:
        contexts.append("activity_hazard")
    if profile and month and month in set(profile.get("local_summer_high_exposure_months", []) + profile.get("known_high_attention_months", [])):
        contexts.append("species_seasonal_overlap")
    if not contexts:
        return 0, None
    points = round(min(8, human_exposure_index * len(contexts) * 1.6), 2)
    return points, {
        "factor": "human_exposure_amplifier",
        "value": human_exposure_index,
        "contexts": contexts,
        "points": points,
        "rationale": "Human exposure amplifies other active signals; exposure alone is not treated as high shark warning.",
    }


def kelp_warning_context_score(
    signals: list[dict[str, Any]],
    *,
    activity_context: str | None,
) -> tuple[float, dict[str, Any] | None, bool]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, None, False
    density_order = {"sparse": 0, "moderate": 1, "dense": 2, "optimal_edge": 3}
    primary = max(public, key=lambda signal: density_order.get(str(signal.get("density_class", "sparse")), 0))
    density = str(primary.get("density_class", "sparse"))
    confidence = max(0.3, min(1.0, float(primary.get("confidence", primary.get("canopy_confidence", 0.45)) or 0.45)))
    base = {"sparse": 0.5, "moderate": 1.5, "dense": 1.8, "optimal_edge": 2.5}.get(density, 0.5)
    contexts = [density]
    if any(signal.get("pinniped_presence") for signal in public):
        base += 0.8
        contexts.append("pinniped_prey_context")
    if (activity_context or "").lower() in {"spearfishing", "diving", "diving_with_catch", "diving with catch", "surfing"}:
        base += 0.7
        contexts.append("human_activity_overlap")
    points = round(min(4, base * confidence), 2)
    return points, {
        "factor": "kelp_forest_habitat_context",
        "value": density,
        "contexts": contexts,
        "points": points,
        "rationale": "Static kelp habitat is bounded environmental context; kelp alone is not treated as a high general warning driver.",
    }, density == "dense"


def hawaii_habitat_warning_context_score(signals: list[dict[str, Any]]) -> tuple[float, list[dict[str, Any]], float]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, [], 0.0

    points = 0.0
    factors: list[dict[str, Any]] = []
    baseline_freshness_points = 0.0

    has_channel = any(signal.get("signal_type") == "reef_channel_habitat" for signal in public)
    has_edge = any(signal.get("signal_type") == "reef_edge_habitat" for signal in public)
    has_shallow = any(signal.get("signal_type") == "shallow_reef_habitat" for signal in public)
    has_hardbottom = any(signal.get("signal_type") == "hardbottom_habitat" for signal in public)
    has_sandy = any(signal.get("signal_type") == "sandy_bottom_habitat" for signal in public)
    has_visibility = any(signal.get("signal_type") == "habitat_visibility_context" for signal in public)

    if has_channel:
        points += 1.2
        factors.append({"factor": "reef_channel_context", "value": True, "points": 1.2, "rationale": "Static reef-channel baseline can modestly inform surveillance-relevant habitat interpretation."})
    if has_edge:
        points += 1.0
        factors.append({"factor": "reef_edge_context", "value": True, "points": 1.0, "rationale": "Static reef-edge baseline provides bounded structural context."})
    if has_shallow:
        points += 0.8
        factors.append({"factor": "shallow_reef_context", "value": True, "points": 0.8, "rationale": "Shallow reef baseline context is included as a low-weight supporting signal."})
    if has_hardbottom:
        points += 0.6
        factors.append({"factor": "hardbottom_context", "value": True, "points": 0.6, "rationale": "Hardbottom baseline contributes modestly to habitat context only."})
    if has_sandy:
        points -= 0.2
        factors.append({"factor": "sandy_bottom_context", "value": True, "points": -0.2, "rationale": "Sandy-bottom baseline generally indicates lower structural complexity."})
    if has_visibility:
        points += 0.5
        factors.append({"factor": "habitat_visibility_context", "value": True, "points": 0.5, "rationale": "Habitat visibility context is baseline-only and bounded."})

    stale_count = sum(1 for signal in public if (signal.get("data_freshness") or {}).get("status") == "stale")
    if stale_count:
        baseline_freshness_points = -0.4
        factors.append(
            {
                "factor": "baseline_habitat_freshness",
                "value": "stale_static_baseline",
                "points": baseline_freshness_points,
                "rationale": "Historic baseline habitat metadata is stale and should reduce confidence in habitat interpretation.",
            }
        )

    return round(max(0.0, min(3.5, points + baseline_freshness_points)), 2), factors, baseline_freshness_points


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
    kelp_habitat_signals: list[dict[str, Any]] | None = None,
    hawaii_habitat_signals: list[dict[str, Any]] | None = None,
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

    regional_sst_score, regional_sst_factor = regional_sst_context_score(profile, sea_surface_temp_c, sst_anomaly_c)
    if regional_sst_factor:
        factors.append(regional_sst_factor)

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

    kelp_signals = kelp_habitat_signals or []
    kelp_score, kelp_factor, dense_kelp_visibility = kelp_warning_context_score(kelp_signals, activity_context=activity_context)
    if kelp_signals:
        data_sources_used.append("kelp_forest_static")
    if kelp_factor:
        factors.append(kelp_factor)

    habitat_signals = hawaii_habitat_signals or []
    habitat_score, habitat_factors, habitat_freshness_penalty = hawaii_habitat_warning_context_score(habitat_signals)
    if habitat_signals:
        data_sources_used.append("hawaii_habitat_static")
    for habitat_factor in habitat_factors:
        factors.append(habitat_factor)

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

    exposure_amp_score, exposure_amp_factor = exposure_amplification_score(
        human_exposure_index=human_exposure_index,
        rain_score=rain_score,
        runoff=runoff,
        sst_score=sst_score,
        regional_sst_score=regional_sst_score,
        bio_score=bio_score,
        alert_score=alert_score,
        activity_context_score=activity_hazard["activity_context_score"],
        profile=profile,
        month=month,
    )
    if exposure_amp_factor:
        factors.append(exposure_amp_factor)

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
    result = {
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
            "kelp_forest_context_score": kelp_score,
            "hawaii_habitat_context_score": habitat_score,
            "weather_alert_score": alert_score,
            "human_exposure_score": human_score,
            "human_exposure_amplifier_score": exposure_amp_score,
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
    if dense_kelp_visibility:
        result["confidence"] = round(max(0.25, result["confidence"] - 0.04), 2)
        result["signals"]["kelp_visibility_confidence_modifier"] = -0.04
    if habitat_freshness_penalty < 0:
        result["confidence"] = round(max(0.25, result["confidence"] + habitat_freshness_penalty), 2)
        result["signals"]["baseline_habitat_freshness_confidence_modifier"] = habitat_freshness_penalty
    return result


def provider_health_document(provider: str, *, status: str, records_ingested: int = 0, last_success: str | None = None) -> dict[str, Any]:
    return {
        "_id": provider,
        "provider": provider,
        "last_success": last_success,
        "records_ingested": records_ingested,
        "status": status,
    }
