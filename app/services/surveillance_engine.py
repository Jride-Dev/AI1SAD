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


def kelp_surveillance_points(
    signals: list[dict[str, Any]],
    *,
    activity_context: str | None,
    biological_events: list[dict[str, Any]],
    human_exposure_index: float | None,
    suspected_species: str | None,
) -> tuple[float, list[str], list[str], bool, float]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, [], [], False, 0.0
    density_rank = {"sparse": 0, "moderate": 1, "dense": 2, "optimal_edge": 3}
    primary = max(public, key=lambda signal: density_rank.get(str(signal.get("density_class", "sparse")), 0))
    density = str(primary.get("density_class", "sparse"))
    signal_types = sorted({str(signal.get("signal_type", "")) for signal in public if signal.get("signal_type")})
    contexts = [density]
    confidence = max(0.3, min(1.0, float(primary.get("confidence", primary.get("canopy_confidence", 0.45)) or 0.45)))
    optimal_kelpedge_score = {"sparse": 0, "moderate": 3, "dense": 1, "optimal_edge": 7}.get(density, 0) * confidence
    points = {"sparse": 2, "moderate": 6, "dense": 7, "optimal_edge": 11}.get(density, 2) * confidence
    pinniped = any(signal.get("pinniped_presence") for signal in public)
    if pinniped:
        points += 5
        contexts.append("pinniped_prey_overlap")
    if any(str(event.get("event_type", "")).lower() in {"seal_presence", "sea_lion_presence", "prey_presence", "baitfish_presence"} for event in biological_events):
        points += 3
        contexts.append("biological_prey_stack")
    if (activity_context or "").lower() in {"spearfishing", "diving", "diving_with_catch", "diving with catch", "surfing"}:
        points += 5
        contexts.append("kelp_human_activity_overlap")
    if "white" in (suspected_species or "").lower() and any(signal.get("signal_type") == "white_shark_kelp_hunting_context" for signal in public):
        points += 3
        contexts.append("white_shark_kelp_context")
    if human_exposure_index and human_exposure_index >= 0.55 and (pinniped or activity_context):
        points += 2
        contexts.append("exposure_overlap")
    return round(min(22, points), 2), signal_types, sorted(set(contexts)), density == "dense", round(min(7.0, optimal_kelpedge_score), 2)


def hawaii_habitat_surveillance_points(
    signals: list[dict[str, Any]],
    *,
    activity_context: str | None,
) -> tuple[float, list[str], list[dict[str, Any]], float]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, [], [], 0.0

    signal_types = sorted({str(signal.get("signal_type", "")) for signal in public if signal.get("signal_type")})
    factors: list[dict[str, Any]] = []
    points = 0.0

    has_channel = "reef_channel_habitat" in signal_types
    has_edge = "reef_edge_habitat" in signal_types
    has_shallow = "shallow_reef_habitat" in signal_types
    has_hardbottom = "hardbottom_habitat" in signal_types
    has_sandy = "sandy_bottom_habitat" in signal_types
    has_visibility = "habitat_visibility_context" in signal_types

    if has_channel:
        points += 5
        factors.append({"factor": "reef_channel_context", "value": True, "points": 5, "rationale": "Baseline reef-channel structure can modestly increase surveillance attention."})
    if has_edge:
        points += 4
        factors.append({"factor": "reef_edge_context", "value": True, "points": 4, "rationale": "Baseline reef-edge structure can support bounded operational mapping attention."})
    if has_shallow:
        points += 3
        factors.append({"factor": "shallow_reef_context", "value": True, "points": 3, "rationale": "Shallow reef baseline adds low-weight context for nearshore monitoring."})
    if has_hardbottom:
        points += 2
        factors.append({"factor": "hardbottom_context", "value": True, "points": 2, "rationale": "Hardbottom baseline provides small structural context."})
    if has_visibility:
        points += 2
        factors.append({"factor": "habitat_visibility_context", "value": True, "points": 2, "rationale": "Visibility-related habitat context supports operational confidence bounds."})
    if has_sandy:
        points -= 1
        factors.append({"factor": "sandy_bottom_context", "value": True, "points": -1, "rationale": "Sandy-bottom baseline generally carries lower structural relevance."})

    if has_channel and (activity_context or "").lower() in {"surfing", "swimming", "diving", "spearfishing"}:
        points += 4
        factors.append({"factor": "channel_activity_stack_context", "value": activity_context, "points": 4, "rationale": "Channel context plus active nearshore activity raises operational attention more than habitat alone."})

    stale_count = sum(1 for signal in public if (signal.get("data_freshness") or {}).get("status") == "stale")
    freshness_penalty = -0.04 if stale_count else 0.0
    if freshness_penalty:
        factors.append({"factor": "baseline_habitat_freshness", "value": "stale_static_baseline", "points": 0, "rationale": "Historic baseline habitat context is stale and reduces confidence."})

    return round(min(18, max(0, points)), 2), signal_types, factors, freshness_penalty


def hawaii_tide_current_surveillance_points(
    signals: list[dict[str, Any]],
    *,
    activity_context: str | None,
    biological_events: list[dict[str, Any]],
    human_exposure_index: float | None,
    verified_sighting_count: int,
) -> tuple[float, list[str], list[dict[str, Any]], float]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, [], [], 0.0

    signal_types = sorted({str(signal.get("signal_type", "")) for signal in public if signal.get("signal_type")})
    factors: list[dict[str, Any]] = []
    points = 0.0
    has_tide = bool({"tide_state_context", "tide_window_context"} & set(signal_types))
    has_current = bool({"nearshore_current_context", "current_direction_context", "current_speed_context"} & set(signal_types))
    has_channel = "channel_flow_context" in signal_types
    has_exchange = "tidal_exchange_context" in signal_types
    water_activity = (activity_context or "").lower() in {"surfing", "swimming", "diving", "spearfishing", "paddling"}
    convergence_context = next(
        (
            signal.get("current_convergence_context")
            for signal in public
            if str(signal.get("current_convergence_context") or "").lower() not in {"", "none", "not_location_specific"}
        ),
        None,
    )
    model_resolution = next((signal.get("nearshore_model_resolution") for signal in public if signal.get("nearshore_model_resolution")), None)
    forecast_freshness = next((signal.get("forecast_freshness") for signal in public if signal.get("forecast_freshness")), None)
    station_gap = next((signal.get("station_coverage_gap") for signal in public if signal.get("station_coverage_gap")), None)
    regional_fallback_used = any(bool(signal.get("regional_fallback_used")) for signal in public)

    if has_tide:
        points += 2
        factors.append({"factor": "tide_state_context", "value": True, "points": 1, "rationale": "Static tide-state context can modestly support observation timing."})
        factors.append({"factor": "tide_window_context", "value": True, "points": 1, "rationale": "Static tide-window context can modestly support observation timing."})
    if has_current:
        points += 3
        factors.append({"factor": "nearshore_current_context", "value": True, "points": 2, "rationale": "Static nearshore-current baseline supports bounded operational mapping."})
        factors.append({"factor": "current_speed_context", "value": True, "points": 1, "rationale": "Static current-speed class is baseline context, not a live measurement."})
    if has_channel:
        points += 4
        factors.append({"factor": "channel_flow_context", "value": True, "points": 4, "rationale": "Static reef-channel flow context can modestly raise surveillance attention."})
    if has_exchange:
        points += 2
        factors.append({"factor": "tidal_exchange_context", "value": True, "points": 2, "rationale": "Tidal-exchange baseline provides supporting observation context."})
    if water_activity and (has_current or has_channel):
        points += 4
        factors.append({"factor": "current_activity_stack_context", "value": activity_context, "points": 4, "rationale": "Current/channel baseline plus water activity raises operational attention more than water movement alone."})
    if verified_sighting_count or biological_events or (human_exposure_index and human_exposure_index >= 0.55):
        points += 2
        factors.append({"factor": "water_movement_signal_stack_context", "value": "stacked_operational_context", "points": 2, "rationale": "Water-movement context is stronger only when paired with sightings, biological events, or human exposure."})
    if convergence_context:
        factors.append({"factor": "current_convergence_context", "value": convergence_context, "points": 0, "rationale": "Convergence context is source metadata only until live current ingestion exists."})
    if model_resolution:
        factors.append({"factor": "nearshore_model_resolution", "value": model_resolution, "points": 0, "rationale": "Model-resolution metadata explains how local or coarse the static baseline is."})
    if forecast_freshness:
        factors.append({"factor": "forecast_freshness", "value": forecast_freshness, "points": 0, "rationale": "Forecast freshness is static/not-live for this adapter."})
    if station_gap:
        factors.append({"factor": "station_coverage_gap", "value": station_gap, "points": 0, "rationale": "Station coverage gaps limit confidence in local surf-line conditions."})
    if regional_fallback_used:
        factors.append({"factor": "regional_fallback_used", "value": True, "points": 0, "rationale": "Regional fallback metadata indicates lower-resolution source context."})

    stale_count = sum(1 for signal in public if (signal.get("data_freshness") or {}).get("status") == "stale" or "static" in str(signal.get("data_freshness_label", "")))
    freshness_penalty = -0.03 if stale_count else 0.0
    if freshness_penalty:
        factors.append({"factor": "baseline_tide_current_freshness", "value": "static_baseline", "points": 0, "rationale": "Static tide/current context is not a live observation and reduces confidence."})

    return round(min(14, max(0, points)), 2), signal_types, factors, freshness_penalty


def hawaii_water_clarity_surveillance_points(
    signals: list[dict[str, Any]],
    *,
    activity_context: str | None,
    biological_events: list[dict[str, Any]],
    human_exposure_index: float | None,
    verified_sighting_count: int,
) -> tuple[float, list[str], list[dict[str, Any]], float]:
    public = [signal for signal in signals if signal.get("visibility", "public") == "public"]
    if not public:
        return 0, [], [], 0.0

    signal_types = sorted({str(signal.get("signal_type", "")) for signal in public if signal.get("signal_type")})
    factors: list[dict[str, Any]] = []
    points = 0.0
    has_clarity = "water_clarity_context" in signal_types
    has_turbidity = "turbidity_context" in signal_types
    has_runoff_visibility = "sediment_runoff_visibility_context" in signal_types
    has_surf_visibility = "surf_zone_visibility_context" in signal_types
    water_activity = (activity_context or "").lower() in {"surfing", "swimming", "diving", "spearfishing", "paddling"}
    turbidity_class = next((signal.get("turbidity_class") for signal in public if signal.get("turbidity_class")), None)
    clarity_class = next((signal.get("clarity_class") for signal in public if signal.get("clarity_class")), None)

    if has_clarity:
        points += 0.5
        factors.append({"factor": "water_clarity_context", "value": clarity_class or True, "points": 0.5, "rationale": "Static clarity baseline modestly informs visibility planning."})
    if has_turbidity:
        points += 1
        factors.append({"factor": "turbidity_context", "value": turbidity_class or True, "points": 1, "rationale": "Static turbidity baseline can reduce confidence and support observation review."})
    if has_runoff_visibility:
        points += 1
        factors.append({"factor": "sediment_runoff_visibility_context", "value": True, "points": 1, "rationale": "Static sediment/runoff visibility context supports bounded observation planning."})
    if has_surf_visibility:
        points += 1
        factors.append({"factor": "surf_zone_visibility_context", "value": True, "points": 1, "rationale": "Surf-zone visibility baseline helps define patrol observation constraints."})
    if water_activity and (has_turbidity or has_surf_visibility):
        points += 2
        factors.append({"factor": "visibility_activity_stack_context", "value": activity_context, "points": 2, "rationale": "Reduced visibility plus water activity raises operational attention more than visibility alone."})
    if verified_sighting_count or biological_events or (human_exposure_index and human_exposure_index >= 0.55):
        points += 1
        factors.append({"factor": "visibility_signal_stack_context", "value": "stacked_operational_context", "points": 1, "rationale": "Visibility context is stronger only when paired with sightings, biological events, or human exposure."})

    stale_count = sum(1 for signal in public if (signal.get("data_freshness") or {}).get("status") == "stale" or "static" in str(signal.get("data_freshness_label", "")))
    freshness_penalty = -0.04 if stale_count else 0.0
    if freshness_penalty:
        factors.append({"factor": "baseline_visibility_freshness", "value": "static_baseline", "points": 0, "rationale": "Static clarity/turbidity context is not a live observation and reduces confidence."})

    return round(min(6, max(0, points)), 2), signal_types, factors, freshness_penalty


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


def recommended_pattern_for(activity_context: str | None, reef_count: int, river_mouth_distance_km: float | None, kelp_contexts: list[str] | None = None) -> str:
    if kelp_contexts and any(context in kelp_contexts for context in {"optimal_edge", "kelp_human_activity_overlap", "pinniped_prey_overlap"}):
        return "kelp-edge expanding grid"
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
    as_of: datetime | None = None,
) -> dict[str, Any]:
    now = as_of or datetime.now(timezone.utc)
    interactions = recent_public_docs(recent_interactions or [], now, lookback_hours)
    sightings = recent_public_docs(sighting_reports or [], now, lookback_hours)
    reefs = [doc for doc in reef_features or [] if doc.get("visibility", "public") == "public"]
    profile = nearest_profile(lat, lon, profiles) if profiles is not None else nearest_profile(lat, lon)
    reef_habitat = bool(reefs)

    warning_inputs = warning_inputs or {}
    warning = calculate_warning(
        lat=lat,
        lon=lon,
        as_of=now,
        lookback_hours=lookback_hours,
        rainfall_72h_mm=warning_inputs.get("rainfall_72h_mm"),
        river_mouth_distance_km=river_mouth_distance_km,
        sea_surface_temp_c=warning_inputs.get("sea_surface_temp_c"),
        sst_anomaly_c=warning_inputs.get("sst_anomaly_c"),
        vessel_activity_index=warning_inputs.get("vessel_activity_index"),
        biological_events=warning_inputs.get("biological_events", []),
        kelp_habitat_signals=warning_inputs.get("kelp_habitat_signals", []),
        hawaii_tide_current_signals=warning_inputs.get("hawaii_tide_current_signals", []),
        hawaii_water_clarity_signals=warning_inputs.get("hawaii_water_clarity_signals", []),
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

    kelp_points, kelp_signal_types, kelp_contexts, dense_kelp_visibility, optimal_kelpedge_score = kelp_surveillance_points(
        warning_inputs.get("kelp_habitat_signals", []),
        activity_context=activity_context,
        biological_events=warning_inputs.get("biological_events", []),
        human_exposure_index=warning_inputs.get("human_exposure_index"),
        suspected_species=suspected_species,
    )
    factors.append(
        {
            "factor": "kelp_forest_surveillance_context",
            "value": kelp_signal_types,
            "contexts": kelp_contexts,
            "points": kelp_points,
            "optimal_kelpedge_score": optimal_kelpedge_score,
            "rationale": "Kelp forest context is bounded habitat information; it raises surveillance attention only when paired with edge habitat, prey, activity, or white shark regional context.",
        }
    )

    habitat_points_score, habitat_signal_types, habitat_factors, habitat_confidence_penalty = hawaii_habitat_surveillance_points(
        warning_inputs.get("hawaii_habitat_signals", []),
        activity_context=activity_context,
    )
    factors.extend(habitat_factors)
    factors.append(
        {
            "factor": "hawaii_habitat_baseline_context",
            "value": habitat_signal_types,
            "points": habitat_points_score,
            "rationale": "Historic Hawaii habitat baselines are bounded structural context and do not represent live observations.",
        }
    )

    tide_current_points, tide_current_signal_types, tide_current_factors, tide_current_confidence_penalty = hawaii_tide_current_surveillance_points(
        warning_inputs.get("hawaii_tide_current_signals", []),
        activity_context=activity_context,
        biological_events=warning_inputs.get("biological_events", []),
        human_exposure_index=warning_inputs.get("human_exposure_index"),
        verified_sighting_count=verified_count,
    )
    factors.extend(tide_current_factors)
    factors.append(
        {
            "factor": "hawaii_tide_current_baseline_context",
            "value": tide_current_signal_types,
            "points": tide_current_points,
            "rationale": "Static PacIOOS/NOAA tide-current baselines are bounded water-movement context and do not represent live observations.",
        }
    )

    water_clarity_points, water_clarity_signal_types, water_clarity_factors, water_clarity_confidence_penalty = hawaii_water_clarity_surveillance_points(
        warning_inputs.get("hawaii_water_clarity_signals", []),
        activity_context=activity_context,
        biological_events=warning_inputs.get("biological_events", []),
        human_exposure_index=warning_inputs.get("human_exposure_index"),
        verified_sighting_count=verified_count,
    )
    factors.extend(water_clarity_factors)
    factors.append(
        {
            "factor": "hawaii_water_clarity_baseline_context",
            "value": water_clarity_signal_types,
            "points": water_clarity_points,
            "rationale": "Static water clarity and turbidity baselines are bounded visibility context and do not represent live observations.",
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
    if warning_inputs.get("kelp_habitat_signals"):
        data_sources_used.add("kelp_forest_static")
    if warning_inputs.get("hawaii_habitat_signals"):
        data_sources_used.add("hawaii_habitat_static")
    if warning_inputs.get("hawaii_tide_current_signals"):
        data_sources_used.add("hawaii_tide_current_static")
    if warning_inputs.get("hawaii_water_clarity_signals"):
        data_sources_used.add("hawaii_water_clarity_static")
    if profile:
        data_sources_used.add("regional_risk_profiles")
    else:
        missing_sources.add("regional_risk_profiles")

    confidence = round(max(0.25, min(0.92, 0.88 - len(missing_sources) * 0.05)), 2)
    if dense_kelp_visibility:
        confidence = round(max(0.25, confidence - 0.04), 2)
    if habitat_confidence_penalty:
        confidence = round(max(0.25, confidence + habitat_confidence_penalty), 2)
    if tide_current_confidence_penalty:
        confidence = round(max(0.25, confidence + tide_current_confidence_penalty), 2)
    if water_clarity_confidence_penalty:
        confidence = round(max(0.25, confidence + water_clarity_confidence_penalty), 2)
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
        "recommended_pattern": recommended_pattern_for(activity_context, len(reefs), river_mouth_distance_km, kelp_contexts),
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
