from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


COUNTRY_ALIASES = {
    "admiralty islands": "papua new guinea",
    "azores": "portugal",
    "british isles": "united kingdom",
    "british west indies": "united kingdom",
    "canary islands": "spain",
    "cape verde": "cabo verde",
    "columbia": "colombia",
    "england": "united kingdom",
    "grand cayman": "cayman islands",
    "hawaii": "united states of america",
    "java": "indonesia",
    "maldives islands": "maldives",
    "okinawa": "japan",
    "palestinian territories": "palestine",
    "reunion": "france",
    "reunion island": "france",
    "san domingo": "dominican republic",
    "scotland": "united kingdom",
    "st helena british overseas territory": "saint helena",
    "st maartin": "saint martin",
    "st kitts nevis": "saint kitts and nevis",
    "tobago": "trinidad and tobago",
    "trinidad tobago": "trinidad and tobago",
    "turks caicos": "turks and caicos islands",
    "turks and caicos": "turks and caicos islands",
    "united arab emirates uae": "united arab emirates",
    "usa": "united states of america",
    "us virgin islands": "united states virgin islands",
    "western samoa": "samoa",
}

COUNTRY_PROPERTY_KEYS = {
    "ADMIN",
    "SOVEREIGNT",
    "NAME",
    "NAME_LONG",
    "FORMAL_EN",
    "BRK_NAME",
    "ISO_A2",
    "ISO_A3",
    "ADM0_A3",
    "SOV_A3",
}


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def field(row: dict[str, Any], *names: str) -> str | None:
    normalized = {normalize(key).replace(" ", ""): value for key, value in row.items()}
    for name in names:
        value = normalized.get(normalize(name).replace(" ", ""))
        if value not in (None, ""):
            return str(value).strip()
    return None


def as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def polygon_parts(geometry: dict[str, Any]) -> Iterable[list[list[list[float]]]]:
    if geometry.get("type") == "Polygon":
        yield geometry["coordinates"]
    elif geometry.get("type") == "MultiPolygon":
        yield from geometry["coordinates"]


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > lat) != (y2 > lat):
            intersect_lon = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < intersect_lon:
                inside = not inside
        previous = current
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    return point_in_ring(lon, lat, polygon[0]) and not any(
        point_in_ring(lon, lat, hole) for hole in polygon[1:]
    )


class CountryBoundaries:
    def __init__(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for feature in payload.get("features", []):
            for key, value in feature.get("properties", {}).items():
                if key in COUNTRY_PROPERTY_KEYS and value:
                    self.by_name[normalize(value)].append(feature)

    def contains(self, country: str, latitude: float, longitude: float) -> bool | None:
        country_name = COUNTRY_ALIASES.get(normalize(country), normalize(country))
        features = self.by_name.get(country_name)
        if not features:
            return None
        return any(
            point_in_polygon(longitude, latitude, polygon)
            for feature in features
            for polygon in polygon_parts(feature["geometry"])
        )


def line_parts(geometry: dict[str, Any]) -> Iterable[list[list[float]]]:
    if geometry.get("type") == "LineString":
        yield geometry["coordinates"]
    elif geometry.get("type") == "MultiLineString":
        yield from geometry["coordinates"]


def segment_distance_km(lat: float, lon: float, a: list[float], b: list[float]) -> float:
    scale_x = 111.32 * max(math.cos(math.radians(lat)), 0.01)
    ax, ay = (a[0] - lon) * scale_x, (a[1] - lat) * 110.57
    bx, by = (b[0] - lon) * scale_x, (b[1] - lat) * 110.57
    dx, dy = bx - ax, by - ay
    denominator = dx * dx + dy * dy
    t = 0.0 if denominator == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / denominator))
    return math.hypot(ax + t * dx, ay + t * dy)


class CoastlineIndex:
    def __init__(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.cells: dict[tuple[int, int], list[tuple[list[float], list[float]]]] = defaultdict(list)
        for feature in payload.get("features", []):
            for line in line_parts(feature["geometry"]):
                for a, b in zip(line, line[1:]):
                    min_lon, max_lon = sorted((a[0], b[0]))
                    min_lat, max_lat = sorted((a[1], b[1]))
                    for cell_lat in range(math.floor(min_lat), math.floor(max_lat) + 1):
                        for cell_lon in range(math.floor(min_lon), math.floor(max_lon) + 1):
                            self.cells[(cell_lat, cell_lon)].append((a, b))

    def distance_km(self, latitude: float, longitude: float) -> float:
        segments: list[tuple[list[float], list[float]]] = []
        origin_lat, origin_lon = math.floor(latitude), math.floor(longitude)
        for cell_lat in range(origin_lat - 1, origin_lat + 2):
            for cell_lon in range(origin_lon - 1, origin_lon + 2):
                segments.extend(self.cells.get((cell_lat, cell_lon), []))
        if not segments:
            return math.inf
        return min(segment_distance_km(latitude, longitude, a, b) for a, b in segments)


def validate(
    input_path: Path,
    output_path: Path,
    countries_path: Path,
    coastline_path: Path,
    minimum_relevance: float = 0.75,
    maximum_coast_distance_km: float = 25.0,
) -> dict[str, int]:
    boundaries = CountryBoundaries(countries_path)
    coastlines = CoastlineIndex(coastline_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    counts: defaultdict[str, int] = defaultdict(int)
    validated_rows: list[dict[str, Any]] = []
    for row in rows:
        if normalize(field(row, "col_1", "query_id")) == "query id":
            continue
        latitude = as_float(field(row, "latitude", "lat"))
        longitude = as_float(field(row, "longitude", "lng", "lon"))
        relevance = as_float(field(row, "relevance", "accuracy_score", "confidence"))
        country = field(row, "col_5", "country") or ""
        status = "validated"
        coast_distance = None
        if latitude is None or longitude is None or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            status = "missing_or_invalid_coordinate"
        elif relevance is not None and relevance < minimum_relevance:
            status = "low_relevance"
        else:
            country_match = boundaries.contains(country, latitude, longitude)
            if country_match is None:
                status = "unknown_country_boundary"
            elif not country_match:
                status = "country_mismatch"
            else:
                coast_distance = coastlines.distance_km(latitude, longitude)
                if coast_distance > maximum_coast_distance_km:
                    status = "too_far_inland"
        counts[status] += 1
        validated_rows.append(
            {
                "query_id": field(row, "col_1", "query_id") or "",
                "location": field(row, "col_3", "location") or "",
                "region": field(row, "col_4", "region") or "",
                "country": country,
                "latitude": "" if latitude is None else latitude,
                "longitude": "" if longitude is None else longitude,
                "relevance": "" if relevance is None else relevance,
                "coast_distance_km": "" if coast_distance is None or not math.isfinite(coast_distance) else round(coast_distance, 3),
                "validation_status": status,
                "provider": "CSV2GEO",
                "provider_country": field(row, "country") or "",
                "provider_match_level": field(row, "match_level") or "",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validated_rows[0].keys())
        writer.writeheader()
        writer.writerows(validated_rows)
    return dict(sorted(counts.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate contextual CSV2GEO results before Incident Globe use.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--countries", type=Path, required=True)
    parser.add_argument("--coastline", type=Path, required=True)
    parser.add_argument("--minimum-relevance", type=float, default=0.75)
    parser.add_argument("--maximum-coast-distance-km", type=float, default=25.0)
    args = parser.parse_args()
    summary = validate(
        args.input,
        args.output,
        args.countries,
        args.coastline,
        args.minimum_relevance,
        args.maximum_coast_distance_km,
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
