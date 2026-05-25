from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.disclaimers import AI1SAD_API_DISCLAIMER
from app.risk_model import band_for_score, haversine_km, nearest_profile, profile_summary
from app.services.activity_hazard import activity_hazard_score
from app.services.warning_engine import calculate_warning, parse_dt


SURVEILLANCE_DISCLAIMER = (
    f"{AI1SAD_API_DISCLAIMER} This drone/search prioritization score supports coastal safety planning "
    "and does not infer shark intent or classify a person as provoking an animal."
)


ACTIVITY_WEIGHTS = {
    "swimming": 4,
    "surfing": 7,
    "spearfishing": 14,
    "diving": 10,
    "fishing": 12,
}


def priority_band(score: float) -> str:
    return band_for_score(score)


def recent_public_docs(docs: list[dict[str, Any]], now: datetime, lookback_hours: int) -> list[dict[str, Any]]:
    cutoff = now - timedelta(hours=lookback_hours)
    recent = []
    for doc in docs:
        if doc.get("visibility", "public") != "public":
            continue
        observed_at = parse_dt(doc.get("observed_at"))
        if observed_at is None or observed_at >= cutoff:
            recent.append(doc)
    return recent


def verified_sighting_count(docs: list[dict[str, Any]]) -> int:
    accepted = {"official", "verified"}
    return sum(1 for doc in docs if str(doc.get("confidence", "")).lower() in accepted or doc.get("verified") is True)


def fatal_interaction_count(docs: list[dict[str, Any]]) -> int:
    return sum(1 for doc in docs if bool(doc.get("fatal")))


def habitat_points(reef_features: list[dict[str, Any]], activity_context: str | None) -> float:
    base = min(15, len(reef_features) * 5)
    if activity_context in {"spearfishing", "diving"} and reef_features:
        base += 8
    return min(24, base)


def activity_points(activity_context: str | None) -> float:
    if not activity_context:
        return 0
    return ACTIVITY_WEIGHTS.get(activity_context.lower(), 5)


def biological_surveillance_points(events: list[dict[str, Any]]) -> tuple[float, list[str]]:
    points = 0.0
    event_types: list[str] = []
    for event in events:
        if event.get("visibility", "public") != "public":
            continue
        event_type = str(event.get("event_type", "")).lower()
        event_types.append(event_type)
        confidence = max(0.5, min(1.0, float(event.get("confidence", 0.5) or 0.5)))
        value = max(0.5, min(1.0, float(event.get("value", 1.0) or 1.0)))
        if "whale_carcass" in event_type or ("whale" in event_type and "carcass" in event_type):
            points = max(points, 18 * confidence * value)
        elif "carcass" in event_type or "fish_kill" in event_type or ("fish" in event_type and "kill" in event_type):
            points = max(points, 16 * confidence * value)
        elif "baitfish" in event_type or "prey" in event_type:
            points = max(points, 9 * confidence * value)
        elif "seal" in event_type or "sea_lion" in event_type:
            points = max(points, 8 * confidence * value)
        elif "turtle" in event_type or "hatchling" in event_type or "migration" in event_type or "nesting" in event_type:
            points = max(points, 6 * confidence * value)
    return round(min(20, points), 2), event_types


def vessel_fishing_surveillance_points(signals: list[dict[str, Any]], *, biological_events: list[dict[str, Any]], human_exposure_index: float | None) -> tuple[float, list[str], list[str]]:
    points = 0.0
    signal_types: list[str] = []
    contexts: list[str] = []
    has_bio = bool(biological_events)
    has_exposure = bool(human_exposure_index and human_exposure_index >= 0.55)
    for signal in signals:
        if signal.get("visibility", "public") != "public":
            continue
        signal_type = str(signal.get("signal_type", "")).lower()
        signal_types.append(signal_type)
        confidence = max(0.5, min(1.0, float(signal.get("confidence", 0.5) or 0.5)))
        value = max(0.0, min(1.0, float(signal.get("value", 0) or 0)))
        if signal_type == "spearfishing_activity":
            candidate = 18 * confidence * max(0.6, value)
            contexts.append("spearfishing_activity")
        elif signal_type in {"fishing_activity", "commercial_fishing_pressure", "recreational_fishing_pressure"}:
            candidate = 12 * confidence * max(0.5, value)
            contexts.append("fishing_pressure")
        elif signal_type in {"pier_fishing_pressure", "marina_boat_pressure"}:
            candidate = 7 * confidence * max(0.4, value)
            contexts.append("pier_marina_baseline")
        elif signal_type in {"dive_boat_activity", "liveaboard_activity"}:
            candidate = 9 * confidence * max(0.4, value)
            contexts.append("dive_boat_liveaboard_context")
        else:
            candidate = 5 * confidence * max(0.4, value)
            contexts.append("vessel_activity")
        if has_bio and has_exposure and signal_type in {"spearfishing_activity", "fishing_activity", "commercial_fishing_pressure", "recreational_fishing_pressure", "pier_fishing_pressure"}:
            candidate += 8
            contexts.append("fishing_biological_exposure_stack")
        elif has_bio and signal_type in {"spearfishing_activity", "fishing_activity", "commercial_fishing_pressure", "recreational_fishing_pressure"}:
            candidate += 4
            contexts.append("fishing_biological_stack")
        points = max(points, candidate)
    return round(min(24, points), 2), signal_types, sorted(set(contexts))


def species_region_points(
    profile: dict[str, Any] | None,
    *,
    suspected_species: str | None,
    activity_context: str | None,
    river_mouth_distance_km: float | None,
    reef_count: int,
    warning_score: float,
    month: int | None,
) -> tuple[float, list[dict[str, Any]]]:
    if not profile:
        return 0, []

    region = profile.get("region_key")
    species = (suspected_species or "").lower()
    points = 0.0
    factors: list[dict[str, Any]] = []

    def add(factor: str, value: Any, pts: float, rationale: str) -> None:
        nonlocal points
        points += pts
        factors.append({"factor": factor, "value": value, "points": pts, "rationale": rationale})

    if suspected_species and suspected_species.lower() in {item.lower() for item in profile.get("dominant_species", [])}:
        add("regional_species_match", suspected_species, 8, "Suspected species is listed in the nearest public regional profile.")

    if region == "western_australia" and ("white" in species or not species):
        if activity_context in {"spearfishing", "diving"} and reef_count:
            add("wa_white_shark_reef_spearfishing_context", activity_context, 18, "Western Australia white shark profile weights reef/spearfishing or diving search context.")
        elif reef_count:
            add("wa_white_shark_reef_context", reef_count, 10, "Western Australia white shark profile weights reef/dropoff habitat.")

    if region == "new_south_wales_australia" and ("bull" in species or not species):
        if river_mouth_distance_km is not None and river_mouth_distance_km <= 5:
            add("nsw_bull_shark_river_runoff_context", river_mouth_distance_km, 18, "NSW bull shark profile weights river-mouth/runoff contexts.")

    if region == "queensland_australia" and ("tiger" in species or "bull" in species or not species):
        if activity_context in {"spearfishing", "diving", "diving_with_catch", "diving with catch"} and reef_count:
            add("queensland_tiger_bull_reef_spearfishing_context", activity_context, 14, "Queensland profile weights tropical reef/spearfishing search context for tiger/bull operational suitability.")
        elif reef_count:
            add("queensland_tropical_reef_context", reef_count, 8, "Queensland profile weights tropical reef habitat for operational search planning.")

    if region == "hawaii" and ("tiger" in species or not species) and month == 10:
        add("hawaii_tiger_shark_october_context", month, 14, "Hawaii tiger shark profile applies October/Sharktober attention context.")

    if region == "florida" and ("bull" in species or "blacktip" in species or not species):
        if activity_context in {"surfing", "fishing"}:
            add("florida_surf_fishing_context", activity_context, 10, "Florida blacktip/bull profile weights surf and fishing exposure.")
        if river_mouth_distance_km is not None and river_mouth_distance_km <= 5:
            add("florida_runoff_river_context", river_mouth_distance_km, 10, "Florida bull shark profile weights river mouth and runoff sensitivity.")

    if warning_score >= 50:
        add("current_warning_context", warning_score, min(12, warning_score / 8), "Current weather/ocean warning score is elevated.")
    if profile and warning_score < 50 and profile.get("region_key") in {"florida", "western_australia", "hawaii", "red_sea"}:
        add("regional_sst_species_context", warning_score, 3, "Regional SST species context can support surveillance review without dominating priority.")

    return min(points, 35), factors


def recommended_pattern_for(activity_context: str | None, reef_count: int, river_mouth_distance_km: float | None) -> str:
    if activity_context in {"spearfishing", "diving", "diving_with_catch", "diving with catch"} and reef_count:
        return "reef-edge expanding grid"
    if river_mouth_distance_km is not None and river_mouth_distance_km <= 5:
        return "river-mouth parallel transects"
    if activity_context in {"surfing", "swimming"}:
        return "surf-zone ladder search"
    return "coastal expanding square"


def score_surveillance_zones(
    *,
    lat: float,
    lon: float,
    radius_km: float,
    mission_type: str,
    lookback_hours: int,
    activity_context: str | None = None,
    suspected_species: str | None = None,
    river_mouth_distance_km: float | None = None,
    month: int | None = None,
    profiles: list[dict[str, Any]] | None = None,
    recent_interactions: list[dict[str, Any]] | None = None,
    sighting_reports: list[dict[str, Any]] | None = None,
    reef_features: list[dict[str, Any]] | None = None,
    warning_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    interactions = recent_public_docs(recent_interactions or [], now, lookback_hours)
    sightings = recent_public_docs(sighting_reports or [], now, lookback_hours)
    reefs = [doc for doc in reef_features or [] if doc.get("visibility", "public") == "public"]
    profile = nearest_profile(lat, lon, profiles) if profiles is not None else nearest_profile(lat, lon)
    reef_habitat = bool(reefs)

    warning_inputs = warning_inputs or {}
    warning = calculate_warning(
        lat=lat,
        lon=lon,
        lookback_hours=lookback_hours,
        rainfall_72h_mm=warning_inputs.get("rainfall_72h_mm"),
        river_mouth_distance_km=river_mouth_distance_km,
        sea_surface_temp_c=warning_inputs.get("sea_surface_temp_c"),
        sst_anomaly_c=warning_inputs.get("sst_anomaly_c"),
        vessel_activity_index=warning_inputs.get("vessel_activity_index"),
        biological_events=warning_inputs.get("biological_events", []),
        human_exposure_index=warning_inputs.get("human_exposure_index"),
        activity_context=activity_context,
        reef_habitat=reef_habitat,
        dropoff_habitat=reef_habitat,
        bait_activity=bool(warning_inputs.get("biological_events")),
        suspected_species=suspected_species,
        month=month,
        profiles=profiles,
        provider_status=warning_inputs.get("provider_status", {}),
    )

    factors: list[dict[str, Any]] = []
    activity_hazard = activity_hazard_score(
        activity_context=activity_context,
        reef_habitat=reef_habitat,
        dropoff_habitat=reef_habitat,
        bait_activity=bool(warning_inputs.get("biological_events")),
        suspected_species=suspected_species,
        regional_profile=profile,
    )

    interaction_points = min(28, len(interactions) * 14 + fatal_interaction_count(interactions) * 8)
    factors.append(
        {
            "factor": "recent_interactions_nearby",
            "value": len(interactions),
            "points": interaction_points,
            "rationale": "Recent public fatal/nonfatal interactions near the mission area increase search priority.",
        }
    )

    verified_count = verified_sighting_count(sightings)
    sighting_points = min(22, verified_count * 11 + max(0, len(sightings) - verified_count) * 4)
    factors.append(
        {
            "factor": "verified_sightings_nearby",
            "value": verified_count,
            "points": sighting_points,
            "rationale": "Verified public sighting reports near the mission area increase search priority.",
        }
    )

    reef_points = habitat_points(reefs, activity_context)
    factors.append(
        {
            "factor": "reef_dropoff_habitat_proximity",
            "value": len(reefs),
            "points": reef_points,
            "rationale": "Reef, dropoff, channel, or habitat features can help define useful drone search zones.",
        }
    )

    river_points = 0
    if river_mouth_distance_km is not None:
        if river_mouth_distance_km <= 1:
            river_points = 16
        elif river_mouth_distance_km <= 5:
            river_points = 11
        elif river_mouth_distance_km <= 10:
            river_points = 5
    factors.append(
        {
            "factor": "river_mouth_runoff_proximity",
            "value": river_mouth_distance_km,
            "points": river_points,
            "rationale": "River mouths, inlets, and runoff zones may deserve targeted search attention where regionally relevant.",
        }
    )

    factors.append(
        {
            "factor": "activity_context",
            "value": activity_context,
            "points": activity_points(activity_context),
            "rationale": "Activity context shapes where a safety team may search; spearfishing is context, not automatic provocation.",
        }
    )
    factors.append(
        {
            "factor": "activity_hazard_score",
            "value": activity_hazard["activity_context_score"],
            "points": round(activity_hazard["activity_context_score"] * 0.35, 2),
            "rationale": "Activity hazard feeds surveillance priority separately from environmental warning score.",
        }
    )

    species_points, species_factors = species_region_points(
        profile,
        suspected_species=suspected_species,
        activity_context=activity_context,
        river_mouth_distance_km=river_mouth_distance_km,
        reef_count=len(reefs),
        warning_score=warning["warning_score"],
        month=month,
    )
    factors.extend(species_factors)
    factors.append(
        {
            "factor": "regional_species_suitability",
            "value": suspected_species,
            "points": species_points,
            "rationale": "Nearest regional profile and suspected species context adjust search priority.",
        }
    )

    bio_points, bio_event_types = biological_surveillance_points(warning_inputs.get("biological_events", []))
    factors.append(
        {
            "factor": "biological_event_surveillance_context",
            "value": bio_event_types,
            "points": bio_points,
            "rationale": "Carcass and fish-kill events have stronger surveillance influence than broad migration or prey context.",
        }
    )

    vessel_fishing_points, vessel_signal_types, vessel_contexts = vessel_fishing_surveillance_points(
        warning_inputs.get("vessel_fishing_signals", []),
        biological_events=warning_inputs.get("biological_events", []),
        human_exposure_index=warning_inputs.get("human_exposure_index"),
    )
    factors.append(
        {
            "factor": "vessel_fishing_surveillance_context",
            "value": vessel_signal_types,
            "contexts": vessel_contexts,
            "points": vessel_fishing_points,
            "rationale": "Fishing, spearfishing, pier, marina, dive-boat, and vessel context primarily affect surveillance priority, not general warning.",
        }
    )

    human_exposure = warning_inputs.get("human_exposure_index")
    human_points = round(min(12, max(0, float(human_exposure or 0)) * 12), 2)
    factors.append(
        {
            "factor": "human_exposure_level",
            "value": human_exposure,
            "points": human_points,
            "rationale": "Human activity level affects search urgency and area selection.",
        }
    )
    exposure_contexts = []
    if human_points and (verified_count or activity_context or interaction_points or warning["warning_score"] >= 25):
        if verified_count:
            exposure_contexts.append("sightings")
        if activity_context:
            exposure_contexts.append("activity_context")
        if interaction_points:
            exposure_contexts.append("recent_interactions")
        if warning["warning_score"] >= 25:
            exposure_contexts.append("environmental_warning_context")
        factors.append(
            {
                "factor": "human_exposure_surveillance_amplifier",
                "value": human_exposure,
                "contexts": exposure_contexts,
                "points": round(min(10, human_points * 0.75), 2),
                "rationale": "Crowding/exposure can raise surveillance priority only when paired with sightings, activity context, recent interactions, or environmental signals.",
            }
        )

    raw_score = sum(float(factor.get("points", 0)) for factor in factors)
    priority_score = min(100, round(raw_score, 2))
    for factor in factors:
        factor["contribution"] = round(float(factor.get("points", 0)) / priority_score, 4) if priority_score else 0
    dominant_factors = sorted(factors, key=lambda item: item.get("points", 0), reverse=True)[:6]

    missing_sources = set(warning.get("missing_data_sources", []))
    data_sources_used = set(warning.get("data_sources_used", []))
    if interactions:
        data_sources_used.add("recent_interactions")
    else:
        missing_sources.add("recent_interactions")
    if sightings:
        data_sources_used.add("sighting_reports")
    else:
        missing_sources.add("sighting_reports")
    if reefs:
        data_sources_used.add("reef_features")
    else:
        missing_sources.add("reef_features")
    if profile:
        data_sources_used.add("regional_risk_profiles")
    else:
        missing_sources.add("regional_risk_profiles")

    confidence = round(max(0.25, min(0.92, 0.88 - len(missing_sources) * 0.05)), 2)
    zone_radius = round(max(0.5, min(radius_km, 2.5 if priority_score >= 50 else 4.0)), 2)
    zone_id = f"{mission_type}:{lat:.3f}:{lon:.3f}:{lookback_hours}:{activity_context or 'general'}"

    zone = {
        "zone_id": zone_id,
        "priority_score": priority_score,
        "priority_band": priority_band(priority_score),
        "surveillance_priority_score": priority_score,
        "surveillance_priority_band": priority_band(priority_score),
        "warning_score": warning["warning_score"],
        "warning_band": warning["warning_band"],
        "activity_context_score": activity_hazard["activity_context_score"],
        "activity_context_band": activity_hazard["activity_context_band"],
        "activity_hazard_factors": activity_hazard["factors"],
        "center": {"geo": {"type": "Point", "coordinates": [lon, lat]}},
        "radius_km": zone_radius,
        "polygon": None,
        "recommended_pattern": recommended_pattern_for(activity_context, len(reefs), river_mouth_distance_km),
        "dominant_factors": dominant_factors,
        "confidence": confidence,
        "data_sources_used": sorted(data_sources_used),
        "missing_data_sources": sorted(missing_sources),
        "regional_profile": profile_summary(profile),
        "mission_type": mission_type,
        "activity_context": activity_context,
        "suspected_species": suspected_species,
        "distance_from_request_km": 0,
        "score_split": {
            "warning_score": "Environmental/live-condition risk from weather, ocean, biological, vessel, and exposure signals.",
            "surveillance_priority_score": "Where safety or drone teams should look first.",
            "activity_hazard_score": "Risk introduced by what the human is doing in context. It is not attack probability.",
        },
        "disclaimer": SURVEILLANCE_DISCLAIMER,
    }

    return {
        "disclaimer": SURVEILLANCE_DISCLAIMER,
        "query": {
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km,
            "mission_type": mission_type,
            "lookback_hours": lookback_hours,
            "activity_context": activity_context,
            "suspected_species": suspected_species,
        },
        "zones": [zone],
    }
