from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GLOBE_SCHEMA_VERSION = "incident_globe_v1"
DEFAULT_DATABASE = Path("data/processed/complete_incidents_scrubbed.sqlite")
DEFAULT_GEOCODE_CACHE = Path("data/raw/geocode_cache.csv")
DEFAULT_CONTEXT_GEOCODES = Path("data/review/incident_globe_context_geocodes_1900_2026.csv")
DEFAULT_HAL_STAGING = Path("data/imports/sharks_happen/staging/latest_sharks_happen_sources.json")
DEFAULT_OUTPUT = Path("data/public/incident_globe_1990_2026.json")

SOURCE_METADATA = {
    "local_legacy_attacks_csv": {"label": "AI1SAD local legacy incident file", "url": None},
    "gsaf_latest_xls": {"label": "Global Shark Attack File", "url": "https://www.sharkattackfile.net/spreadsheets/GSAF5.xls"},
    "github_n_enzer_attacks_csv": {"label": "N-Enzer SharkAttackAnalysis mirror", "url": "https://github.com/N-Enzer/SharkAttackAnalysis"},
    "github_ordovas_attacks_csv": {"label": "Ordovas shark-attack mirror", "url": "https://github.com/ordovas/pandas-project"},
    "github_ordovas_clean_csv": {"label": "Ordovas cleaned shark-attack mirror", "url": "https://github.com/ordovas/pandas-project"},
    "australian_shark_incident_database": {"label": "Australian Shark-Incident Database", "url": "https://github.com/cjabradshaw/AustralianSharkIncidentDatabase"},
    "sharks_happen": {"label": "Hal / Sharks Happen Stats", "url": "https://www.youtube.com/@sharkshappen"},
}

NO_INJURY_PATTERNS = (
    "no injury",
    "no injuries",
    "not injured",
    "uninjured",
    "without injury",
)

CONSUMED_PATTERNS = (
    "body not recovered",
    "body was not recovered",
    "remains not recovered",
    "presumed eaten",
    "presumed consumed",
    "swallowed whole",
)

# Broad envelopes only gate approximate cache matches. Source-provided coordinates
# remain untouched, and ambiguous cache points become unresolved rather than guessed.
COUNTRY_COORDINATE_BOUNDS: dict[str, tuple[tuple[float, float, float, float], ...]] = {
    "australia": (
        (-44.5, -9.0, 112.0, 154.5),
        (-11.5, -9.5, 105.0, 106.5),
        (-13.0, -11.0, 96.0, 97.5),
    ),
    "ecuador": ((-5.5, 2.0, -82.0, -75.0), (-2.0, 2.0, -93.0, -88.0)),
    "fiji": ((-21.0, -12.0, 176.0, 180.0), (-21.0, -12.0, -180.0, -177.0)),
    "mauritius": ((-21.0, -18.5, 56.0, 58.0), (-20.5, -18.5, 63.0, 64.5)),
    "new zealand": ((-48.0, -33.0, 165.0, 180.0), (-48.0, -33.0, -180.0, -175.0)),
    "puerto rico": ((17.5, 18.7, -67.5, -65.0),),
    "reunion": ((-22.0, -20.0, 54.0, 56.0),),
    "south africa": ((-35.5, -22.0, 16.0, 33.5),),
    "st helena british overseas territory": (
        (-17.0, -15.0, -6.5, -4.5),
        (-8.5, -7.0, -15.0, -13.0),
        (-38.5, -36.5, -13.0, -11.0),
    ),
    "st maartin": ((18.0, 18.2, -63.2, -62.8),),
    "st maarten": ((18.0, 18.2, -63.2, -62.8),),
    "usa": (
        (24.0, 50.0, -125.0, -66.0),
        (51.0, 72.0, -180.0, -129.0),
        (51.0, 72.0, 170.0, 180.0),
        (18.0, 23.0, -161.0, -154.0),
        (13.0, 21.0, 144.0, 146.0),
        (-15.0, -10.0, -172.0, -168.0),
        (17.5, 18.6, -65.2, -64.0),
    ),
    "united states": (
        (24.0, 50.0, -125.0, -66.0),
        (51.0, 72.0, -180.0, -129.0),
        (51.0, 72.0, 170.0, 180.0),
        (18.0, 23.0, -161.0, -154.0),
        (13.0, 21.0, 144.0, 146.0),
        (-15.0, -10.0, -172.0, -168.0),
        (17.5, 18.6, -65.2, -64.0),
    ),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "y"}
    return bool(value)


def as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def location_key(value: Any) -> str:
    text = (clean_text(value) or "").casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def coordinate_matches_country(latitude: float, longitude: float, country: Any) -> bool:
    bounds = COUNTRY_COORDINATE_BOUNDS.get(location_key(country))
    if not bounds:
        return True
    return any(
        min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon
        for min_lat, max_lat, min_lon, max_lon in bounds
    )


def valid_coordinate(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def load_geocode_cache(path: str | Path) -> dict[str, tuple[float, float, bool]]:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    result: dict[str, tuple[float, float, bool]] = {}
    with cache_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if valid_coordinate(row.get("Latitude"), row.get("Longitude")):
                review_status = location_key(row.get("ReviewStatus") or row.get("review_status"))
                reviewed = review_status in {"approved", "reviewed", "verified"}
                result[location_key(row.get("Location"))] = (
                    float(row["Latitude"]),
                    float(row["Longitude"]),
                    reviewed,
                )
    return result


def contextual_key(location: Any, region: Any, country: Any) -> tuple[str, str, str]:
    return location_key(location), location_key(region), location_key(country)


def load_context_geocodes(path: str | Path) -> dict[tuple[str, str, str], tuple[float, float, float | None]]:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    result: dict[tuple[str, str, str], tuple[float, float, float | None]] = {}
    with cache_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("validation_status") != "validated":
                continue
            if not valid_coordinate(row.get("latitude"), row.get("longitude")):
                continue
            relevance = None
            try:
                relevance = float(row["relevance"]) if row.get("relevance") else None
            except ValueError:
                pass
            result[contextual_key(row.get("location"), row.get("region"), row.get("country"))] = (
                float(row["latitude"]),
                float(row["longitude"]),
                relevance,
            )
    return result


def load_source_rows(path: str | Path, start_year: int, end_year: int) -> list[dict[str, Any]]:
    with sqlite3.connect(Path(path)) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT * FROM incidents_scrubbed WHERE year BETWEEN ? AND ?"
        return [dict(row) for row in connection.execute(query, (start_year, end_year))]


def provocation_label(values: list[Any]) -> tuple[str, bool]:
    labels: set[str] = set()
    for value in values:
        text = (clean_text(value) or "").casefold()
        if "unprovoked" in text:
            labels.add("unprovoked")
        elif text == "provoked" or text.startswith("provoked "):
            labels.add("provoked")
    if len(labels) > 1:
        return "conflicted", True
    return (next(iter(labels)), False) if labels else ("unknown", False)


def explicitly_invalid(record: dict[str, Any]) -> bool:
    incident_type = (clean_text(record.get("incident_type")) or "").casefold()
    species = (clean_text(record.get("species_common")) or "").casefold()
    return incident_type == "invalid" or species in {"no shark involvement", "not a shark"}


def source_ref(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("source_name") or "unknown")
    metadata = SOURCE_METADATA.get(name, {"label": name.replace("_", " ").title(), "url": None})
    return {
        "source_name": name,
        "source_label": metadata["label"],
        "source_record_id": clean_text(row.get("source_record_id")),
        "source_row_number": row.get("source_row_number"),
        "url": metadata["url"],
        "url_scope": "dataset" if metadata["url"] else None,
        "match_status": "canonical" if not as_bool(row.get("is_duplicate")) else "deduplicated_source_row",
    }


def unique_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    sources: list[dict[str, Any]] = []
    for row in rows:
        source = source_ref(row)
        key = (source["source_name"], source["source_record_id"], source["source_row_number"])
        if key not in seen:
            seen.add(key)
            sources.append(source)
    return sources


def outcome_category(fatal: bool, injury: Any, hal_records: list[dict[str, Any]] | None = None) -> str:
    injury_text = (clean_text(injury) or "").casefold()
    if fatal:
        for record in hal_records or []:
            raw = record.get("raw_claims", {})
            swallowed = str(raw.get("Swallowed Whole") or "").strip().casefold() in {"yes", "y", "true", "1"}
            consumed_claim = record.get("consumption_attempt_claim") is True
            combined = " ".join(filter(None, [injury_text, (clean_text(record.get("injury_raw")) or "").casefold()]))
            if swallowed or (consumed_claim and any(marker in combined for marker in CONSUMED_PATTERNS)):
                return "fatal_consumed"
        return "fatal"
    if any(marker in injury_text for marker in NO_INJURY_PATTERNS):
        return "no_injury"
    return "non_fatal"


def coordinates_for_record(
    record: dict[str, Any],
    geocodes: dict[str, tuple[float, float, bool]],
    context_geocodes: dict[tuple[str, str, str], tuple[float, float, float | None]] | None = None,
) -> tuple[dict[str, Any] | None, str, str]:
    if valid_coordinate(record.get("latitude"), record.get("longitude")):
        return (
            {"type": "Point", "coordinates": [float(record["longitude"]), float(record["latitude"])]},
            "source_coordinate",
            "reviewed_source",
        )
    context = (context_geocodes or {}).get(
        contextual_key(
            record.get("location_public") or record.get("location_raw"),
            record.get("area") or record.get("area_raw"),
            record.get("country") or record.get("country_normalized") or record.get("country_raw"),
        )
    )
    if context:
        lat, lon, relevance = context
        confidence = "high_contextual" if relevance is not None and relevance >= 0.9 else "reviewed_contextual"
        return {"type": "Point", "coordinates": [lon, lat]}, "csv2geo_contextual", confidence
    cached = geocodes.get(location_key(record.get("location_public") or record.get("location_raw")))
    if cached:
        lat, lon, reviewed = cached
        if not reviewed:
            return None, "unreviewed_geocode_rejected", "unknown"
        country = record.get("country") or record.get("country_normalized") or record.get("country_raw")
        if not coordinate_matches_country(lat, lon, country):
            return None, "country_mismatch_rejected", "unknown"
        return {"type": "Point", "coordinates": [lon, lat]}, "local_geocode_cache", "approximate"
    return None, "unresolved", "unknown"


def hal_source_ref(record: dict[str, Any], match_status: str) -> dict[str, Any]:
    metadata = SOURCE_METADATA["sharks_happen"]
    return {
        "source_name": "sharks_happen",
        "source_label": metadata["label"],
        "source_record_id": record.get("source_record_id"),
        "source_row_number": record.get("source_row_number"),
        "url": metadata["url"],
        "url_scope": "channel",
        "match_status": match_status,
    }


def load_hal_records(path: str | Path, start_year: int, end_year: int) -> list[dict[str, Any]]:
    staging_path = Path(path)
    if not staging_path.exists():
        return []
    payload = json.loads(staging_path.read_text(encoding="utf-8"))
    return [
        record
        for record in payload.get("records", [])
        if isinstance(record.get("year"), int) and start_year <= record["year"] <= end_year
    ]


def build_globe_dataset(
    *,
    database_path: str | Path = DEFAULT_DATABASE,
    geocode_cache_path: str | Path = DEFAULT_GEOCODE_CACHE,
    context_geocode_path: str | Path = DEFAULT_CONTEXT_GEOCODES,
    hal_staging_path: str | Path = DEFAULT_HAL_STAGING,
    start_year: int = 1990,
    end_year: int = 2026,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = load_source_rows(database_path, start_year, end_year)
    geocodes = load_geocode_cache(geocode_cache_path)
    context_geocodes = load_context_geocodes(context_geocode_path)
    root_by_record = {row["record_id"]: row.get("duplicate_of") or row["record_id"] for row in rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    base_by_root: dict[str, dict[str, Any]] = {}
    for row in rows:
        root = root_by_record[row["record_id"]]
        grouped[root].append(row)
        if not as_bool(row.get("is_duplicate")):
            base_by_root[root] = row

    hal_records = load_hal_records(hal_staging_path, start_year, end_year)
    hal_by_root: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hal_standalone: list[dict[str, Any]] = []
    for record in hal_records:
        review = record.get("duplicate_review", {})
        candidates = review.get("cross_source_candidates") or []
        candidate_id = candidates[0].get("candidate_record_id") if candidates else None
        root = root_by_record.get(candidate_id)
        if review.get("status") == "exact_candidate" and root in base_by_root:
            hal_by_root[root].append(record)
        else:
            hal_standalone.append(record)

    records: list[dict[str, Any]] = []
    excluded_invalid_records = 0
    for root, base in sorted(base_by_root.items(), key=lambda item: (as_int(item[1].get("year")) or 0, item[0])):
        if explicitly_invalid(base):
            excluded_invalid_records += 1
            continue
        supporting_rows = grouped[root]
        hal_matches = hal_by_root.get(root, [])
        year = as_int(base.get("year"))
        if year is None:
            continue
        coordinates, coordinate_source, coordinate_confidence = coordinates_for_record(base, geocodes, context_geocodes)
        provocation, provocation_conflict = provocation_label([row.get("incident_type") for row in supporting_rows])
        sources = unique_sources(supporting_rows)
        sources.extend(hal_source_ref(record, "exact_candidate") for record in hal_matches)
        records.append(
            {
                "globe_id": f"incident:{root}",
                "canonical_record_id": root,
                "year": year,
                "decade": year // 10 * 10,
                "date_text": clean_text(base.get("date_text")),
                "month": as_int(base.get("month")),
                "day": as_int(base.get("day")),
                "country": clean_text(base.get("country")),
                "region": clean_text(base.get("area")),
                "location": clean_text(base.get("location_public")),
                "coordinates": coordinates,
                "mapped": coordinates is not None,
                "coordinate_source": coordinate_source,
                "coordinate_confidence": coordinate_confidence,
                "activity": clean_text(base.get("activity")),
                "incident_type_raw": clean_text(base.get("incident_type")),
                "provocation": provocation,
                "provocation_conflict": provocation_conflict,
                "injury_summary": clean_text(base.get("injury_summary")),
                "fatal": as_bool(base.get("fatal")),
                "outcome_category": outcome_category(as_bool(base.get("fatal")), base.get("injury_summary"), hal_matches),
                "species_common": clean_text(base.get("species_common")),
                "species_scientific": clean_text(base.get("species_scientific")),
                "sources": sources,
                "source_count": len(sources),
                "media": [],
                "visibility": "local_review",
            }
        )

    for record in hal_standalone:
        coordinates, coordinate_source, coordinate_confidence = coordinates_for_record(record, geocodes, context_geocodes)
        records.append(
            {
                "globe_id": f"incident:{record['source_record_id']}",
                "canonical_record_id": None,
                "year": record["year"],
                "decade": int(record["year"] // 10 * 10),
                "date_text": record.get("incident_date_raw"),
                "month": record.get("month"),
                "day": record.get("day"),
                "country": record.get("country_normalized") or record.get("country_raw"),
                "region": record.get("area_raw"),
                "location": record.get("location_raw"),
                "coordinates": coordinates,
                "mapped": coordinates is not None,
                "coordinate_source": coordinate_source,
                "coordinate_confidence": coordinate_confidence,
                "activity": record.get("activity_raw"),
                "incident_type_raw": None,
                "provocation": "unknown",
                "provocation_conflict": False,
                "injury_summary": record.get("injury_raw"),
                "fatal": record.get("fatality_claim") is True,
                "outcome_category": outcome_category(record.get("fatality_claim") is True, record.get("injury_raw"), [record]),
                "species_common": record.get("shark_label_raw"),
                "species_scientific": None,
                "sources": [hal_source_ref(record, record.get("duplicate_review", {}).get("status", "unmatched"))],
                "source_count": 1,
                "media": [],
                "visibility": "local_review",
            }
        )

    records.sort(key=lambda item: (item["year"], item.get("date_text") or "", item["globe_id"]), reverse=True)
    outcome_counts = Counter(record["outcome_category"] for record in records)
    provocation_counts = Counter(record["provocation"] for record in records)
    decade_counts = Counter(record["decade"] for record in records)
    mapped_count = sum(record["mapped"] for record in records)
    country_mismatch_rejections = sum(
        record["coordinate_source"] == "country_mismatch_rejected" for record in records
    )
    unreviewed_geocode_rejections = sum(
        record["coordinate_source"] == "unreviewed_geocode_rejected" for record in records
    )
    contextual_geocode_count = sum(record["coordinate_source"] == "csv2geo_contextual" for record in records)
    return {
        "schema_version": GLOBE_SCHEMA_VERSION,
        "generated_at": generated_at or utc_now_iso(),
        "range": {"start_year": start_year, "end_year": end_year},
        "summary": {
            "total_records": len(records),
            "mapped_records": mapped_count,
            "unmapped_records": len(records) - mapped_count,
            "outcome_counts": dict(sorted(outcome_counts.items())),
            "provocation_counts": dict(sorted(provocation_counts.items())),
            "decade_counts": {str(key): value for key, value in sorted(decade_counts.items())},
            "hal_records_considered": len(hal_records),
            "hal_exact_matches_attached": sum(len(items) for items in hal_by_root.values()),
            "hal_standalone_records": len(hal_standalone),
            "explicit_invalid_records_excluded": excluded_invalid_records,
            "country_mismatch_coordinates_rejected": country_mismatch_rejections,
            "unreviewed_geocode_coordinates_rejected": unreviewed_geocode_rejections,
            "contextual_geocode_coordinates_mapped": contextual_geocode_count,
        },
        "data_boundaries": {
            "victim_names_included": False,
            "automatic_duplicate_merges": False,
            "unresolved_locations_guessed": False,
            "source_labels_are_confirmed_facts": False,
            "media_invented": False,
            "explicit_invalid_rows_included": False,
            "approximate_cache_coordinates_country_checked": True,
            "unreviewed_cache_coordinates_plotted": False,
            "contextual_geocodes_require_country_and_coast_validation": True,
        },
        "records": records,
    }


def write_dataset(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")


def persist_dataset(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    from app.mongodb import COLLECTIONS

    collection = db[COLLECTIONS["incident_globe"]]
    collection.delete_many({"year": {"$gte": payload["range"]["start_year"], "$lte": payload["range"]["end_year"]}})
    if payload["records"]:
        collection.insert_many(payload["records"], ordered=False)
    build_id = f"incident_globe_{payload['range']['start_year']}_{payload['range']['end_year']}"
    db["dataset_builds"].replace_one(
        {"_id": build_id},
        {"_id": build_id, **{key: value for key, value in payload.items() if key != "records"}},
        upsert=True,
    )
    return {"records_inserted": len(payload["records"]), "collection": COLLECTIONS["incident_globe"]}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the AI1SAD 1990-2026 incident globe dataset.")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE))
    parser.add_argument("--geocode-cache", default=str(DEFAULT_GEOCODE_CACHE))
    parser.add_argument("--context-geocodes", default=str(DEFAULT_CONTEXT_GEOCODES))
    parser.add_argument("--hal-staging", default=str(DEFAULT_HAL_STAGING))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--mongo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    payload = build_globe_dataset(
        database_path=args.database,
        geocode_cache_path=args.geocode_cache,
        context_geocode_path=args.context_geocodes,
        hal_staging_path=args.hal_staging,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    write_dataset(args.output, payload)
    result: dict[str, Any] = {"output": args.output, **payload["summary"]}
    if args.mongo:
        from app.mongodb import ensure_incident_globe_indexes, get_database

        database = get_database()
        ensure_incident_globe_indexes(database)
        result["mongo"] = persist_dataset(database, payload)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
