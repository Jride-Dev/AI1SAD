from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.replay.confidence import ConfidenceDecomposition
from app.replay.decay import apply_decay_to_signals
from app.replay.heatmap import HeatmapConfig, HeatmapGenerator
from app.replay.quiet_day import QuietDayBaseline
from app.replay.scenarios import REPLAY_SCENARIOS, ReplayScenario
from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


SCENARIO_ID = "queensland_spearfishing_reef_tiger_bull_2026"
ASSET_DIR = ROOT / "docs" / "assets" / "case_studies"


def reef_features(scenario: ReplayScenario) -> list[dict[str, Any]]:
    if not (scenario.reef_habitat or scenario.dropoff_habitat):
        return []
    return [
        {
            "visibility": "public",
            "feature_type": "reef" if scenario.reef_habitat else "dropoff",
            "name": scenario.reef_feature_name or "Replay reef/dropoff habitat context",
            "location": {"geo": {"type": "Point", "coordinates": [scenario.lon, scenario.lat]}},
        }
    ]


def warning_inputs(scenario: ReplayScenario) -> dict[str, Any]:
    return {
        "rainfall_72h_mm": scenario.rainfall_72h_mm,
        "sea_surface_temp_c": scenario.sea_surface_temp_c,
        "sst_anomaly_c": scenario.sst_anomaly_c,
        "vessel_activity_index": scenario.vessel_activity_index,
        "biological_events": scenario.biological_events,
        "human_exposure_index": scenario.human_exposure_index,
    }


def run_case_study(scenario: ReplayScenario) -> dict[str, Any]:
    warning = calculate_warning(
        lat=scenario.lat,
        lon=scenario.lon,
        lookback_hours=scenario.lookback_hours,
        rainfall_72h_mm=scenario.rainfall_72h_mm,
        river_mouth_distance_km=scenario.river_mouth_distance_km,
        sea_surface_temp_c=scenario.sea_surface_temp_c,
        sst_anomaly_c=scenario.sst_anomaly_c,
        vessel_activity_index=scenario.vessel_activity_index,
        biological_events=scenario.biological_events,
        human_exposure_index=scenario.human_exposure_index,
        activity_context=scenario.activity_context,
        reef_habitat=scenario.reef_habitat,
        dropoff_habitat=scenario.dropoff_habitat,
        bait_activity=bool(scenario.biological_events),
        suspected_species=scenario.suspected_species,
        month=scenario.month,
        profiles=REGIONAL_RISK_PROFILES,
    )
    surveillance = score_surveillance_zones(
        lat=scenario.lat,
        lon=scenario.lon,
        radius_km=scenario.radius_km,
        mission_type="replay_case_study",
        lookback_hours=scenario.lookback_hours,
        activity_context=scenario.activity_context,
        suspected_species=scenario.suspected_species,
        river_mouth_distance_km=scenario.river_mouth_distance_km,
        month=scenario.month,
        profiles=REGIONAL_RISK_PROFILES,
        reef_features=reef_features(scenario),
        warning_inputs=warning_inputs(scenario),
    )["zones"][0]

    baseline = QuietDayBaseline()
    quiet_warning = baseline.baseline_warning(
        lat=scenario.lat,
        lon=scenario.lon,
        month=scenario.month,
        profiles=REGIONAL_RISK_PROFILES,
    )
    quiet_comparison = baseline.compare(current=warning, baseline=quiet_warning)
    confidence = ConfidenceDecomposition().decompose(
        data_sources_used=surveillance.get("data_sources_used", []),
        missing_data_sources=surveillance.get("missing_data_sources", []),
    )

    decay_now = scenario.timestamp.replace(hour=min(scenario.timestamp.hour + 6, 23))
    decayed_signals = apply_decay_to_signals(
        [
            {
                "signal_type": "spearfishing_activity",
                "timestamp": scenario.timestamp.isoformat(),
                "value": 1.0,
                "visibility": "public",
            },
            {
                "signal_type": "vessel_activity",
                "timestamp": scenario.timestamp.isoformat(),
                "value": scenario.vessel_activity_index,
                "visibility": "public",
            },
            {
                "signal_type": "ocean_sst",
                "timestamp": scenario.timestamp.isoformat(),
                "value": scenario.sea_surface_temp_c,
                "visibility": "public",
            },
            *[
                {
                    "signal_type": "biological_event",
                    "timestamp": event.get("observed_at", scenario.timestamp.isoformat()),
                    "value": event.get("value", 1.0),
                    "visibility": event.get("visibility", "public"),
                }
                for event in scenario.biological_events
            ],
        ],
        now=decay_now,
    )

    return {
        "scenario": {
            "scenario_id": scenario.scenario_id,
            "label": scenario.label,
            "timestamp": scenario.timestamp.isoformat(),
            "coordinates": {"lat": scenario.lat, "lon": scenario.lon},
            "approximate_region": "Kennedy Shoal / Great Barrier Reef, Far North Queensland, Australia",
            "activity_context": scenario.activity_context,
            "suspected_species_context": ["tiger shark", "bull shark"],
            "reef_habitat": scenario.reef_habitat,
            "dropoff_habitat": scenario.dropoff_habitat,
        },
        "warning": warning,
        "surveillance": surveillance,
        "quiet_day_comparison": quiet_comparison,
        "confidence_breakdown": confidence,
        "signal_decay": decayed_signals,
        "disclaimer": warning["disclaimer"],
    }


def factor_summary(replay: dict[str, Any]) -> dict[str, Any]:
    surveillance = replay["surveillance"]
    warning = replay["warning"]
    return {
        "scenario_id": replay["scenario"]["scenario_id"],
        "score_summary": {
            "warning_score": warning["warning_score"],
            "warning_band": warning["warning_band"],
            "activity_hazard_score": warning["activity_context_score"],
            "activity_hazard_band": warning["activity_context_band"],
            "surveillance_priority_score": surveillance["surveillance_priority_score"],
            "surveillance_priority_band": surveillance["surveillance_priority_band"],
        },
        "dominant_surveillance_factors": surveillance["dominant_factors"],
        "dominant_warning_factors": warning["dominant_factors"],
        "score_split": surveillance["score_split"],
    }


def generate_heatmap(scenario: ReplayScenario) -> dict[str, Any]:
    config = HeatmapConfig(center_lat=scenario.lat, center_lon=scenario.lon, radius_km=18.0, grid_points=9)
    generator = HeatmapGenerator(config)

    def scorer(lat: float, lon: float) -> dict[str, Any]:
        zone = score_surveillance_zones(
            lat=lat,
            lon=lon,
            radius_km=scenario.radius_km,
            mission_type="replay_heatmap",
            lookback_hours=scenario.lookback_hours,
            activity_context=scenario.activity_context,
            suspected_species=scenario.suspected_species,
            river_mouth_distance_km=scenario.river_mouth_distance_km,
            month=scenario.month,
            profiles=REGIONAL_RISK_PROFILES,
            reef_features=reef_features(scenario),
            warning_inputs=warning_inputs(scenario),
        )["zones"][0]
        return {
            "surveillance_priority_score": zone["surveillance_priority_score"],
            "surveillance_priority_band": zone["surveillance_priority_band"],
            "warning_score": zone["warning_score"],
            "warning_band": zone["warning_band"],
            "activity_context_score": zone["activity_context_score"],
            "activity_context_band": zone["activity_context_band"],
        }

    heatmap = generator.generate(scorer)
    heatmap["score_type"] = "surveillance_priority_score"
    heatmap["scenario_id"] = scenario.scenario_id
    return heatmap


def cell_color(score: float) -> str:
    if score >= 75:
        return "#b42318"
    if score >= 50:
        return "#d97706"
    if score >= 25:
        return "#f2c94c"
    return "#2f80ed"


def write_heatmap_svg(heatmap: dict[str, Any], replay: dict[str, Any], path: Path) -> None:
    cells = heatmap["cells"]
    lats = [cell["lat"] for cell in cells]
    lons = [cell["lon"] for cell in cells]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    width, height = 980, 640
    plot_x, plot_y, plot_w, plot_h = 70, 110, 560, 420

    def sx(lon: float) -> float:
        return plot_x + ((lon - min_lon) / max(max_lon - min_lon, 0.0001)) * plot_w

    def sy(lat: float) -> float:
        return plot_y + (1 - ((lat - min_lat) / max(max_lat - min_lat, 0.0001))) * plot_h

    warning = replay["warning"]
    surveillance = replay["surveillance"]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="640" viewBox="0 0 980 640" role="img" aria-label="AI1SAD Queensland spearfishing replay surveillance heatmap">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#17202a}.title{font-size:25px;font-weight:700}.subtitle{font-size:14px;fill:#4b5563}.label{font-size:12px;fill:#344054}.score{font-size:18px;font-weight:700}.small{font-size:11px;fill:#667085}.callout{font-size:14px;font-weight:700}",
        "</style>",
        '<rect width="980" height="640" fill="#fbfcfe" />',
        '<text x="46" y="42" class="title">AI1SAD replay: Queensland spearfishing incident, May 2026</text>',
        '<text x="46" y="68" class="subtitle">Surveillance-priority heatmap around Kennedy Shoal / Far North Queensland. Not attack probability.</text>',
        f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="#ffffff" stroke="#d0d5dd" />',
    ]
    for cell in cells:
        score = float(cell["surveillance_priority_score"])
        svg.append(
            f'<circle cx="{sx(cell["lon"]):.1f}" cy="{sy(cell["lat"]):.1f}" r="13" fill="{cell_color(score)}" fill-opacity="0.72">'
            f'<title>{cell["lat"]}, {cell["lon"]}: surveillance_priority_score {score:.1f}</title></circle>'
        )
    svg.extend(
        [
            f'<circle cx="{sx(replay["scenario"]["coordinates"]["lon"]):.1f}" cy="{sy(replay["scenario"]["coordinates"]["lat"]):.1f}" r="7" fill="#111827" />',
            f'<text x="{sx(replay["scenario"]["coordinates"]["lon"]) + 12:.1f}" y="{sy(replay["scenario"]["coordinates"]["lat"]) - 8:.1f}" class="callout">incident coordinates</text>',
            '<text x="70" y="560" class="small">Blue low, yellow moderate, orange elevated, red high surveillance priority.</text>',
            '<rect x="680" y="112" width="245" height="292" fill="#fff" stroke="#d0d5dd" rx="8" />',
            '<text x="704" y="146" class="callout">Replay score split</text>',
            f'<text x="704" y="184" class="label">warning_score</text><text x="880" y="184" text-anchor="end" class="score">{warning["warning_score"]:.0f}</text>',
            f'<text x="704" y="222" class="label">activity_hazard_score</text><text x="880" y="222" text-anchor="end" class="score">{warning["activity_context_score"]:.0f}</text>',
            f'<text x="704" y="260" class="label">surveillance_priority_score</text><text x="880" y="260" text-anchor="end" class="score">{surveillance["surveillance_priority_score"]:.0f}</text>',
            f'<text x="704" y="304" class="label">confidence</text><text x="880" y="304" text-anchor="end" class="score">{surveillance["confidence"]:.2f}</text>',
            f'<text x="704" y="348" class="label">recommended pattern</text>',
            f'<text x="704" y="370" class="small">{surveillance["recommended_pattern"]}</text>',
            '<text x="46" y="610" class="small">AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def main() -> None:
    scenario = REPLAY_SCENARIOS[SCENARIO_ID]
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    replay = run_case_study(scenario)
    heatmap = generate_heatmap(scenario)
    factors = factor_summary(replay)

    replay_path = ASSET_DIR / "queensland_spearfishing_2026_replay.json"
    heatmap_json_path = ASSET_DIR / "queensland_spearfishing_2026_heatmap.json"
    factors_path = ASSET_DIR / "queensland_spearfishing_2026_factors.json"
    heatmap_svg_path = ASSET_DIR / "queensland_spearfishing_2026_heatmap.svg"

    replay_path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
    heatmap_json_path.write_text(json.dumps(heatmap, indent=2), encoding="utf-8")
    factors_path.write_text(json.dumps(factors, indent=2), encoding="utf-8")
    write_heatmap_svg(heatmap, replay, heatmap_svg_path)

    print(
        json.dumps(
            {
                "scenario_id": SCENARIO_ID,
                "warning_score": replay["warning"]["warning_score"],
                "activity_hazard_score": replay["warning"]["activity_context_score"],
                "surveillance_priority_score": replay["surveillance"]["surveillance_priority_score"],
                "assets": [
                    str(replay_path),
                    str(heatmap_json_path),
                    str(factors_path),
                    str(heatmap_svg_path),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
