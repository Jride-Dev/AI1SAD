from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any


RISK_DISCLAIMER = (
    "This is a first-pass shark encounter-risk estimate for research and planning. "
    "It is not an attack prediction, safety guarantee, or substitute for local lifeguard, "
    "weather, beach-closure, or wildlife guidance."
)


@dataclass(frozen=True)
class FactorScore:
    factor: str
    value: Any
    points: float
    max_points: float
    rationale: str


RISK_FACTOR_DEFINITIONS = [
    {
        "factor": "historical_incident_density",
        "max_points": 20,
        "description": "Nearby public historical incident density within the requested radius.",
        "assumptions": "Past incident density can indicate recurring overlap among sharks, people, and reporting patterns.",
    },
    {
        "factor": "recent_rainfall_runoff",
        "max_points": 15,
        "description": "Recent rainfall as a proxy for runoff, turbidity, and organic discharge.",
        "assumptions": "Heavy rainfall can reduce visibility and increase runoff near shore.",
    },
    {
        "factor": "river_mouth_distance",
        "max_points": 15,
        "description": "Distance to the nearest river mouth, inlet, estuary, or major outflow.",
        "assumptions": "River mouths can concentrate nutrients, prey, turbidity, and predator movement.",
    },
    {
        "factor": "sea_surface_temperature_species_suitability",
        "max_points": 10,
        "description": "Sea surface temperature and season as coarse suitability signals for common coastal shark presence.",
        "assumptions": "Moderate to warm coastal temperatures can align with seasonal habitat suitability.",
    },
    {
        "factor": "fishing_activity",
        "max_points": 10,
        "description": "Observed or inferred fishing activity near the location.",
        "assumptions": "Fishing can introduce bait, hooked fish, discards, and scent cues.",
    },
    {
        "factor": "baitfish_prey_indicator",
        "max_points": 10,
        "description": "Observed baitfish, schooling fish, birds feeding, or other prey indicators.",
        "assumptions": "Prey concentration can increase predator presence.",
    },
    {
        "factor": "water_visibility",
        "max_points": 10,
        "description": "Low water visibility as a proxy for reduced detectability and mistaken-identity conditions.",
        "assumptions": "Turbid water can increase encounter uncertainty.",
    },
    {
        "factor": "human_water_activity",
        "max_points": 10,
        "description": "Relative intensity of swimming, surfing, diving, or other in-water activity.",
        "assumptions": "More people in the water increases opportunity for encounters.",
    },
]


REGIONAL_RISK_PROFILES = [
    {
        "_id": "florida",
        "region_key": "florida",
        "name": "Florida",
        "visibility": "public",
        "center": {"name": "Florida Atlantic coast", "geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
        "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
        "known_high_attention_months": [3, 4, 10],
        "dominant_species": ["blacktip shark", "spinner shark", "bull shark", "tiger shark"],
        "species_weights": {"bull shark": 1.0, "blacktip shark": 0.8, "spinner shark": 0.7, "tiger shark": 0.6},
        "species_environmental_triggers": {
            "bull shark": {"river_mouth": 1.25, "rainfall_runoff": 1.25, "low_visibility": 1.15},
            "blacktip shark": {"baitfish_prey_indicator": 1.2, "human_exposure": 1.1},
        },
        "species_specific_risk_factors": {
            "blacktip shark": ["seasonal nearshore migration", "baitfish schools"],
            "bull shark": ["river mouths", "turbid water", "rainfall runoff"],
        },
        "environmental_multipliers": {
            "summer": 1.08,
            "high_attention": 1.05,
            "rainfall_runoff": 1.08,
            "river_mouth": 1.07,
        },
        "human_exposure_multipliers": {
            "weekend": 1.15,
            "non_summer_tourist": 1.08,
            "beach_exposure": 1.1,
        },
        "warning_cache_ttl_minutes": 30,
        "notes": "Florida has strong beach exposure outside summer as well as weekend/tourist pulses.",
        "citations": ["Florida Museum ISAF regional incident context", "GSAF public incident records"],
    },
    {
        "_id": "hawaii",
        "region_key": "hawaii",
        "name": "Hawaii",
        "visibility": "public",
        "center": {"name": "Hawaii", "geo": {"type": "Point", "coordinates": [-157.8, 21.3]}},
        "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
        "known_high_attention_months": [10],
        "dominant_species": ["tiger shark", "reef shark", "galapagos shark"],
        "species_weights": {"tiger shark": 1.0, "reef shark": 0.5, "galapagos shark": 0.5},
        "species_environmental_triggers": {
            "tiger shark": {"sharktober": 1.3, "prey_indicator": 1.2, "rainfall_runoff": 1.1},
        },
        "species_specific_risk_factors": {
            "tiger shark": ["fall seasonal attention", "turtle/prey movement", "murky runoff"],
        },
        "environmental_multipliers": {
            "summer": 1.05,
            "high_attention": 1.2,
            "sharktober": 1.25,
            "rainfall_runoff": 1.08,
        },
        "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.08},
        "warning_cache_ttl_minutes": 30,
        "notes": "October receives a Hawaii-specific Sharktober seasonal multiplier.",
        "citations": ["Hawaii DLNR shark safety context", "GSAF public incident records"],
    },
    {
        "_id": "new_south_wales_australia",
        "region_key": "new_south_wales_australia",
        "name": "New South Wales, Australia",
        "visibility": "public",
        "center": {"name": "New South Wales coast", "geo": {"type": "Point", "coordinates": [151.2, -33.9]}},
        "local_summer_high_exposure_months": [12, 1, 2],
        "known_high_attention_months": [1, 2, 3],
        "dominant_species": ["white shark", "bull shark", "tiger shark"],
        "species_weights": {"white shark": 1.0, "bull shark": 0.9, "whaler shark": 0.8, "tiger shark": 0.5},
        "species_environmental_triggers": {
            "bull shark": {"river_mouth": 1.2, "rainfall_runoff": 1.15},
            "white shark": {"prey_indicator": 1.2, "sst_score": 1.1},
        },
        "species_specific_risk_factors": {
            "white shark": ["temperate coastal habitat", "seal/prey overlap"],
            "bull shark": ["estuaries", "river mouths", "warm turbid water"],
        },
        "environmental_multipliers": {
            "summer": 1.18,
            "high_attention": 1.12,
            "australia_jan_feb": 1.18,
            "river_mouth": 1.08,
        },
        "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.12},
        "warning_cache_ttl_minutes": 45,
        "notes": "Southern Hemisphere summer is December-February; January-February get explicit high-exposure handling.",
        "citations": ["Australian Shark-Incident Database", "GSAF public incident records"],
    },
    {
        "_id": "western_australia",
        "region_key": "western_australia",
        "name": "Western Australia",
        "visibility": "public",
        "center": {"name": "Western Australia coast", "geo": {"type": "Point", "coordinates": [115.86, -31.95]}},
        "local_summer_high_exposure_months": [12, 1, 2],
        "known_high_attention_months": [1, 2, 3],
        "dominant_species": ["white shark", "tiger shark"],
        "species_weights": {"white shark": 1.0, "tiger shark": 0.7},
        "species_environmental_triggers": {
            "white shark": {"prey_indicator": 1.2, "sst_score": 1.1},
            "tiger shark": {"fishing_activity": 1.15},
        },
        "species_specific_risk_factors": {
            "white shark": ["temperate coast", "offshore islands", "prey overlap"],
            "tiger shark": ["warm coastal waters", "fishing activity"],
        },
        "environmental_multipliers": {"summer": 1.16, "high_attention": 1.12, "australia_jan_feb": 1.18},
        "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.1},
        "warning_cache_ttl_minutes": 45,
        "notes": "Southern Hemisphere summer profile with January-February high-exposure handling.",
        "citations": ["Australian Shark-Incident Database", "GSAF public incident records"],
    },
    {
        "_id": "california",
        "region_key": "california",
        "name": "California",
        "visibility": "public",
        "center": {"name": "California coast", "geo": {"type": "Point", "coordinates": [-120.5, 35.4]}},
        "local_summer_high_exposure_months": [6, 7, 8, 9],
        "known_high_attention_months": [8, 9, 10],
        "dominant_species": ["white shark"],
        "species_weights": {"white shark": 1.0},
        "species_environmental_triggers": {"white shark": {"prey_indicator": 1.2, "sst_score": 1.1}},
        "species_specific_risk_factors": {
            "white shark": ["temperate water", "pinniped/prey overlap", "surf zones"],
        },
        "environmental_multipliers": {"summer": 1.08, "high_attention": 1.1, "prey_indicator": 1.08},
        "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.08},
        "warning_cache_ttl_minutes": 60,
        "notes": "California emphasizes white shark habitat and late-summer/fall attention months.",
        "citations": ["California shark incident public records", "GSAF public incident records"],
    },
    {
        "_id": "south_africa",
        "region_key": "south_africa",
        "name": "South Africa",
        "visibility": "public",
        "center": {"name": "South Africa coast", "geo": {"type": "Point", "coordinates": [18.5, -34.1]}},
        "local_summer_high_exposure_months": [12, 1, 2],
        "known_high_attention_months": [1, 2, 12],
        "dominant_species": ["white shark", "bronze whaler", "bull shark", "tiger shark"],
        "species_weights": {"white shark": 1.0, "bronze whaler": 0.8, "bull shark": 0.7, "tiger shark": 0.5},
        "species_environmental_triggers": {
            "white shark": {"prey_indicator": 1.2},
            "bronze whaler": {"baitfish_prey_indicator": 1.2, "fishing_activity": 1.1},
        },
        "species_specific_risk_factors": {
            "white shark": ["temperate coast", "seal/prey overlap"],
            "bull shark": ["warm water", "river mouths"],
        },
        "environmental_multipliers": {"summer": 1.12, "high_attention": 1.08, "prey_indicator": 1.08},
        "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.1},
        "warning_cache_ttl_minutes": 60,
        "notes": "Southern Hemisphere summer profile with region-specific dominant species.",
        "citations": ["South African public incident records", "GSAF public incident records"],
    },
    {
        "_id": "red_sea",
        "region_key": "red_sea",
        "name": "Red Sea",
        "visibility": "public",
        "center": {"name": "Central Red Sea", "geo": {"type": "Point", "coordinates": [38.5, 20.5]}},
        "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
        "known_high_attention_months": [6, 7, 8, 9, 10],
        "dominant_species": ["oceanic whitetip shark", "tiger shark", "mako shark"],
        "species_weights": {"oceanic whitetip shark": 1.0, "tiger shark": 0.7, "mako shark": 0.5},
        "species_environmental_triggers": {
            "oceanic whitetip shark": {"feeding_event": 1.35, "shipping_activity": 1.2, "offshore_exposure": 1.2},
            "tiger shark": {"carcass_report": 1.2, "prey_indicator": 1.1},
        },
        "species_specific_risk_factors": {
            "oceanic whitetip shark": ["feeding-event sensitivity", "shipping influence", "offshore human exposure"],
        },
        "environmental_multipliers": {"summer": 1.1, "high_attention": 1.12, "prey_indicator": 1.12},
        "human_exposure_multipliers": {"weekend": 1.05, "beach_exposure": 1.08},
        "warning_cache_ttl_minutes": 30,
        "notes": "Red Sea profile emphasizes oceanic whitetip anomalies, feeding-event sensitivity, and shipping influence.",
        "citations": ["Regional public incident context", "GSAF public incident records"],
    },
]


def clamp(value: float, low: float = 0, high: float = 1) -> float:
    return max(low, min(high, value))


def band_for_score(score: float) -> str:
    if score < 25:
        return "low"
    if score < 50:
        return "moderate"
    if score < 75:
        return "elevated"
    return "high"


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_km = 6371
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def nearest_profile(lat: float, lon: float, profiles: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    candidates = profiles or REGIONAL_RISK_PROFILES
    public_profiles = [profile for profile in candidates if profile.get("visibility", "public") == "public"]
    if not public_profiles:
        return None
    return min(
        public_profiles,
        key=lambda profile: haversine_km(
            lon,
            lat,
            profile["center"]["geo"]["coordinates"][0],
            profile["center"]["geo"]["coordinates"][1],
        ),
    )


def profile_summary(profile: dict[str, Any] | None) -> dict[str, Any] | None:
    if not profile:
        return None
    return {
        "region_key": profile.get("region_key"),
        "name": profile.get("name"),
        "local_summer_high_exposure_months": profile.get("local_summer_high_exposure_months", []),
        "known_high_attention_months": profile.get("known_high_attention_months", []),
        "dominant_species": profile.get("dominant_species", []),
        "species_weights": profile.get("species_weights", {}),
        "warning_cache_ttl_minutes": profile.get("warning_cache_ttl_minutes", 60),
        "notes": profile.get("notes"),
        "citations": profile.get("citations", []),
    }


def regional_adjustments(
    base_score: float,
    factors: list[dict[str, Any]],
    profile: dict[str, Any] | None,
    *,
    month: int | None,
    weekend: bool = False,
    human_water_activity: float = 0,
    recent_rainfall_mm_24h: float = 0,
    river_mouth_distance_km: float | None = None,
    baitfish_prey_indicator: float = 0,
) -> tuple[float, list[dict[str, Any]], float]:
    if not profile:
        return base_score, factors, 0.55

    adjusted = base_score
    factor_list = list(factors)
    multipliers = profile.get("environmental_multipliers", {})
    human_multipliers = profile.get("human_exposure_multipliers", {})
    confidence = 0.72

    def apply_multiplier(name: str, multiplier: float, value: Any, rationale: str) -> None:
        nonlocal adjusted
        before = adjusted
        adjusted = round(adjusted * multiplier, 2)
        factor_list.append(
            {
                "factor": name,
                "value": value,
                "points": round(adjusted - before, 2),
                "max_points": 25,
                "rationale": rationale,
            }
        )

    if month in profile.get("local_summer_high_exposure_months", []):
        apply_multiplier(
            "regional_summer_high_exposure",
            multipliers.get("summer", 1.0),
            month,
            "Uses the local regional summer/high-exposure calendar, not a global summer definition.",
        )

    if month in profile.get("known_high_attention_months", []):
        apply_multiplier(
            "regional_high_attention_month",
            multipliers.get("high_attention", 1.0),
            month,
            "Known regional high-attention month for encounter monitoring.",
        )

    if profile.get("region_key") == "hawaii" and month == 10:
        apply_multiplier("hawaii_sharktober", multipliers.get("sharktober", 1.0), month, "Hawaii October Sharktober seasonal multiplier.")

    if profile.get("region_key") in {"new_south_wales_australia", "western_australia"} and month in {1, 2}:
        apply_multiplier(
            "australia_jan_feb_high_exposure",
            multipliers.get("australia_jan_feb", 1.0),
            month,
            "Australia January-February high-exposure/high-attention seasonal handling.",
        )

    if profile.get("region_key") == "florida" and weekend:
        apply_multiplier("florida_weekend_exposure", human_multipliers.get("weekend", 1.0), weekend, "Florida weekend beach-exposure multiplier.")

    if profile.get("region_key") == "florida" and month and month not in profile.get("local_summer_high_exposure_months", []):
        apply_multiplier(
            "florida_non_summer_tourist_exposure",
            human_multipliers.get("non_summer_tourist", 1.0),
            month,
            "Florida non-summer tourism and beach exposure remain meaningful.",
        )

    if recent_rainfall_mm_24h >= 25:
        apply_multiplier("regional_rainfall_runoff", multipliers.get("rainfall_runoff", 1.0), recent_rainfall_mm_24h, "Regional runoff sensitivity.")

    if river_mouth_distance_km is not None and river_mouth_distance_km <= 5:
        apply_multiplier("regional_river_mouth", multipliers.get("river_mouth", 1.0), river_mouth_distance_km, "Regional river-mouth sensitivity.")

    if baitfish_prey_indicator >= 0.5:
        apply_multiplier("regional_prey_indicator", multipliers.get("prey_indicator", 1.0), baitfish_prey_indicator, "Regional prey-signal sensitivity.")

    if human_water_activity >= 0.5:
        apply_multiplier("regional_beach_exposure", human_multipliers.get("beach_exposure", 1.0), human_water_activity, "Regional human beach/water exposure multiplier.")

    return min(round(adjusted, 2), 100), factor_list, confidence


def score_risk(
    *,
    historical_incident_count: int = 0,
    recent_rainfall_mm_24h: float = 0,
    river_mouth_distance_km: float | None = None,
    sea_surface_temp_c: float | None = None,
    fishing_activity: float = 0,
    baitfish_prey_indicator: float = 0,
    water_visibility_m: float | None = None,
    human_water_activity: float = 0,
    month: int | None = None,
    weekend: bool = False,
    regional_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    factors: list[FactorScore] = []

    historical_points = round(clamp(historical_incident_count / 20) * 20, 2)
    factors.append(
        FactorScore(
            "historical_incident_density",
            historical_incident_count,
            historical_points,
            20,
            "More nearby public historical incidents increase the baseline encounter signal.",
        )
    )

    if recent_rainfall_mm_24h >= 50:
        rainfall_points = 15
    elif recent_rainfall_mm_24h >= 25:
        rainfall_points = 10
    elif recent_rainfall_mm_24h >= 10:
        rainfall_points = 5
    else:
        rainfall_points = 0
    factors.append(
        FactorScore(
            "recent_rainfall_runoff",
            recent_rainfall_mm_24h,
            rainfall_points,
            15,
            "Recent rainfall is treated as a runoff and turbidity proxy.",
        )
    )

    if river_mouth_distance_km is None:
        river_points = 0
    elif river_mouth_distance_km <= 1:
        river_points = 15
    elif river_mouth_distance_km <= 5:
        river_points = 10
    elif river_mouth_distance_km <= 10:
        river_points = 5
    else:
        river_points = 0
    factors.append(
        FactorScore(
            "river_mouth_distance",
            river_mouth_distance_km,
            river_points,
            15,
            "Closer river mouths, estuaries, or outflows increase the environmental encounter signal.",
        )
    )

    if sea_surface_temp_c is None:
        temp_points = 0
    elif 20 <= sea_surface_temp_c <= 28:
        temp_points = 10
    elif 15 <= sea_surface_temp_c < 20 or 28 < sea_surface_temp_c <= 31:
        temp_points = 5
    else:
        temp_points = 0
    if month in {6, 7, 8, 9, 10} and temp_points:
        temp_points = min(10, temp_points + 2)
    factors.append(
        FactorScore(
            "sea_surface_temperature_species_suitability",
            sea_surface_temp_c,
            temp_points,
            10,
            "Coarse seasonal and temperature suitability signal for coastal species presence.",
        )
    )

    fishing_points = round(clamp(fishing_activity) * 10, 2)
    factors.append(
        FactorScore(
            "fishing_activity",
            fishing_activity,
            fishing_points,
            10,
            "Fishing activity can add bait, scent, discards, or hooked fish cues.",
        )
    )

    prey_points = round(clamp(baitfish_prey_indicator) * 10, 2)
    factors.append(
        FactorScore(
            "baitfish_prey_indicator",
            baitfish_prey_indicator,
            prey_points,
            10,
            "Baitfish, birds feeding, or prey concentration can increase predator presence.",
        )
    )

    if water_visibility_m is None:
        visibility_points = 0
    elif water_visibility_m < 1:
        visibility_points = 10
    elif water_visibility_m < 3:
        visibility_points = 6
    elif water_visibility_m < 5:
        visibility_points = 3
    else:
        visibility_points = 0
    factors.append(
        FactorScore(
            "water_visibility",
            water_visibility_m,
            visibility_points,
            10,
            "Lower visibility increases uncertainty and reduces detection distance.",
        )
    )

    human_points = round(clamp(human_water_activity) * 10, 2)
    factors.append(
        FactorScore(
            "human_water_activity",
            human_water_activity,
            human_points,
            10,
            "More people in the water increases opportunity for encounters.",
        )
    )

    score = round(sum(factor.points for factor in factors), 2)
    factor_dicts = [factor.__dict__ for factor in factors]
    warning_score, adjusted_factors, confidence = regional_adjustments(
        score,
        factor_dicts,
        regional_profile,
        month=month,
        weekend=weekend,
        human_water_activity=human_water_activity,
        recent_rainfall_mm_24h=recent_rainfall_mm_24h,
        river_mouth_distance_km=river_mouth_distance_km,
        baitfish_prey_indicator=baitfish_prey_indicator,
    )
    return {
        "score": score,
        "band": band_for_score(score),
        "warning_score": warning_score,
        "warning_band": band_for_score(warning_score),
        "confidence": confidence,
        "factors": adjusted_factors,
        "regional_profile": profile_summary(regional_profile),
        "dominant_contributing_factors": sorted(adjusted_factors, key=lambda factor: factor["points"], reverse=True)[:5],
        "disclaimer": RISK_DISCLAIMER,
    }
