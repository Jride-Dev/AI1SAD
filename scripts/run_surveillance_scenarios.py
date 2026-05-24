from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning


HORSESHOE_REEF_SCENARIOS = [
    {
        "label": "Horseshoe Reef\nspearfishing",
        "short_label": "Horseshoe Reef",
        "lat": -31.9826564,
        "lon": 115.5153234,
        "activity_context": "spearfishing",
        "suspected_species": "white shark",
        "reef_habitat": True,
        "month": 5,
        "notes": "Reported activity/site context: spearfishing on reef habitat in Western Australia white shark suitability.",
    },
    {
        "label": "Geordie Bay\nswimming",
        "short_label": "Geordie Bay",
        "lat": -31.9943,
        "lon": 115.5488,
        "activity_context": "swimming",
        "suspected_species": "white shark",
        "reef_habitat": False,
        "month": 5,
        "notes": "Nearby beach-water comparison with the same regional species context but lower activity hazard.",
    },
    {
        "label": "Rocky Bay\nshoreline",
        "short_label": "Rocky Bay",
        "lat": -32.0007,
        "lon": 115.5231,
        "activity_context": "swimming",
        "suspected_species": None,
        "reef_habitat": False,
        "month": 5,
        "notes": "Nearby shoreline comparison without reef/spearfishing/known species inputs.",
    },
    {
        "label": "West End reef\ndiving",
        "short_label": "West End Reef",
        "lat": -32.0111,
        "lon": 115.4525,
        "activity_context": "diving_with_catch",
        "suspected_species": "white shark",
        "reef_habitat": True,
        "month": 5,
        "notes": "Nearby reef/dropoff comparison with catch-handling activity but not the incident coordinates.",
    },
]


def reef_docs(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    if not scenario["reef_habitat"]:
        return []
    return [
        {
            "visibility": "public",
            "feature_type": "reef",
            "name": f"{scenario['short_label']} reef/habitat feature",
            "location": {"geo": {"type": "Point", "coordinates": [scenario["lon"], scenario["lat"]]}},
        }
    ]


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    warning = calculate_warning(
        lat=scenario["lat"],
        lon=scenario["lon"],
        activity_context=scenario["activity_context"],
        reef_habitat=scenario["reef_habitat"],
        dropoff_habitat=scenario["reef_habitat"],
        suspected_species=scenario["suspected_species"],
        month=scenario["month"],
        profiles=REGIONAL_RISK_PROFILES,
    )
    surveillance = score_surveillance_zones(
        lat=scenario["lat"],
        lon=scenario["lon"],
        radius_km=10,
        mission_type="drone_search",
        lookback_hours=72,
        activity_context=scenario["activity_context"],
        suspected_species=scenario["suspected_species"],
        month=scenario["month"],
        profiles=REGIONAL_RISK_PROFILES,
        reef_features=reef_docs(scenario),
    )["zones"][0]
    return {
        **scenario,
        "warning_score": warning["warning_score"],
        "warning_band": warning["warning_band"],
        "activity_context_score": warning["activity_context_score"],
        "activity_context_band": warning["activity_context_band"],
        "surveillance_priority_score": surveillance["surveillance_priority_score"],
        "surveillance_priority_band": surveillance["surveillance_priority_band"],
        "confidence": surveillance["confidence"],
        "recommended_pattern": surveillance["recommended_pattern"],
        "dominant_factors": surveillance["dominant_factors"],
        "score_split": surveillance["score_split"],
    }


def bar(svg: list[str], *, x: int, y: float, width: int, height: int, color: str, label: str) -> None:
    bar_height = max(1, int((y / 100) * height))
    top = 250 - bar_height
    svg.append(f'<rect x="{x}" y="{top}" width="{width}" height="{bar_height}" fill="{color}" rx="3" />')
    svg.append(f'<text x="{x + width / 2}" y="{top - 6}" text-anchor="middle" class="score">{y:.0f}</text>')
    svg.append(f'<text x="{x + width / 2}" y="274" text-anchor="middle" class="label">{label}</text>')


def write_svg(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="620" viewBox="0 0 1120 620" role="img" aria-label="AI1SAD Horseshoe Reef model replay comparison">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#17202a}.title{font-size:26px;font-weight:700}.subtitle{font-size:14px;fill:#445}.axis{stroke:#ccd;stroke-width:1}.score{font-size:13px;font-weight:700}.label{font-size:12px}.small{font-size:11px;fill:#556}.legend{font-size:13px}.callout{font-size:15px;font-weight:700}",
        "</style>",
        '<rect width="1120" height="620" fill="#fbfcfe" />',
        '<text x="40" y="42" class="title">AI1SAD model replay: Horseshoe Reef, May 16 2026</text>',
        '<text x="40" y="68" class="subtitle">Low environmental warning can coexist with high activity hazard and high drone/surveillance priority.</text>',
        '<line x1="60" y1="250" x2="1060" y2="250" class="axis" />',
        '<line x1="60" y1="50" x2="60" y2="250" class="axis" />',
        '<text x="40" y="254" text-anchor="end" class="small">0</text>',
        '<text x="40" y="154" text-anchor="end" class="small">50</text>',
        '<text x="40" y="54" text-anchor="end" class="small">100</text>',
        '<line x1="55" y1="150" x2="1060" y2="150" stroke="#eef" stroke-width="1" />',
        '<circle cx="70" cy="310" r="6" fill="#4c78a8" /><text x="84" y="314" class="legend">warning_score: environmental/live-condition risk</text>',
        '<circle cx="390" cy="310" r="6" fill="#f58518" /><text x="404" y="314" class="legend">activity_context_score: risk introduced by what the human is doing</text>',
        '<circle cx="790" cy="310" r="6" fill="#54a24b" /><text x="804" y="314" class="legend">surveillance_priority_score: where drone teams should look first</text>',
    ]
    start_x = 110
    group_width = 238
    bar_width = 42
    for index, row in enumerate(results):
        x = start_x + index * group_width
        bar(svg, x=x, y=row["warning_score"], width=bar_width, height=200, color="#4c78a8", label="warn")
        bar(svg, x=x + 52, y=row["activity_context_score"], width=bar_width, height=200, color="#f58518", label="activity")
        bar(svg, x=x + 104, y=row["surveillance_priority_score"], width=bar_width, height=200, color="#54a24b", label="priority")
        for line_no, line in enumerate(row["label"].split("\n")):
            svg.append(f'<text x="{x + 72}" y="{350 + line_no * 16}" text-anchor="middle" class="label">{line}</text>')
        svg.append(f'<text x="{x + 72}" y="390" text-anchor="middle" class="small">{row["recommended_pattern"]}</text>')
    incident = results[0]
    svg.extend(
        [
            '<rect x="40" y="430" width="1040" height="135" fill="#fff" stroke="#dde3ea" rx="8" />',
            '<text x="64" y="462" class="callout">Horseshoe Reef split</text>',
            f'<text x="64" y="490" class="subtitle">warning_score {incident["warning_score"]:.0f}/100 ({incident["warning_band"]}) stays low because no live weather/ocean/biological/vessel signals are present in this replay.</text>',
            f'<text x="64" y="516" class="subtitle">activity_context_score {incident["activity_context_score"]:.0f}/100 ({incident["activity_context_band"]}) rises from spearfishing + reef/dropoff + Western Australia white shark suitability.</text>',
            f'<text x="64" y="542" class="subtitle">surveillance_priority_score {incident["surveillance_priority_score"]:.0f}/100 ({incident["surveillance_priority_band"]}) says this is where drone/safety teams should look first.</text>',
            '<text x="64" y="590" class="small">Not attack probability. Deterministic replay using current AI1SAD rules and public/reported scenario context.</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI1SAD surveillance model replay scenarios.")
    parser.add_argument("--output-dir", default="docs/assets")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [run_scenario(scenario) for scenario in HORSESHOE_REEF_SCENARIOS]
    json_path = output_dir / "horseshoe_reef_2026_model_replay.json"
    svg_path = output_dir / "horseshoe_reef_2026_model_replay.svg"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_svg(results, svg_path)
    print(json.dumps({"scenarios": len(results), "json": str(json_path), "svg": str(svg_path)}, indent=2))


if __name__ == "__main__":
    main()
