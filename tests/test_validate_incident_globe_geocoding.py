from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.validate_incident_globe_geocoding import validate


def write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


def test_validation_accepts_coastal_country_match_and_rejects_bad_points(tmp_path: Path):
    input_path = tmp_path / "results.csv"
    output_path = tmp_path / "validated.csv"
    countries_path = tmp_path / "countries.geojson"
    coastline_path = tmp_path / "coastline.geojson"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["query_id", "location", "region", "country", "Latitude", "Longitude", "Relevance"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {"query_id": "good", "location": "Beach", "region": "State", "country": "Testland", "Latitude": 1, "Longitude": 1, "Relevance": 0.9},
                {"query_id": "wrong", "location": "Beach", "region": "State", "country": "Testland", "Latitude": 20, "Longitude": 20, "Relevance": 0.9},
                {"query_id": "weak", "location": "Beach", "region": "State", "country": "Testland", "Latitude": 1, "Longitude": 1, "Relevance": 0.2},
            ]
        )
    write_geojson(
        countries_path,
        [{"type": "Feature", "properties": {"ADMIN": "Testland"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}}],
    )
    write_geojson(
        coastline_path,
        [{"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [[0, 0], [0, 2]]}}],
    )

    summary = validate(input_path, output_path, countries_path, coastline_path, maximum_coast_distance_km=120)
    rows = {row["query_id"]: row for row in csv.DictReader(output_path.open(encoding="utf-8-sig"))}

    assert summary == {"country_mismatch": 1, "low_relevance": 1, "validated": 1}
    assert rows["good"]["validation_status"] == "validated"
    assert rows["good"]["coast_distance_km"]
