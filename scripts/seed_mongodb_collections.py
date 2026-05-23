from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo import MongoClient, ReplaceOne

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mongodb import COLLECTIONS, ensure_mongodb_indexes
from scripts.load_mongodb import load_env


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def clean_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def clean_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def public_geo(lat: Any, lon: Any) -> dict[str, Any] | None:
    latitude = clean_float(lat)
    longitude = clean_float(lon)
    if latitude is None or longitude is None:
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return {"type": "Point", "coordinates": [longitude, latitude]}


def incident_document(row: dict[str, Any]) -> dict[str, Any]:
    geo = public_geo(row.get("latitude"), row.get("longitude"))
    location = {"name": row.get("location_public") or None}
    if geo:
        location["geo"] = geo
    return {
        "_id": row["record_id"],
        "record_id": row["record_id"],
        "canonical_key": row.get("canonical_key"),
        "visibility": "public",
        "date": {
            "text": row.get("date_text") or None,
            "year": clean_int(row.get("year")),
            "month": clean_int(row.get("month")),
            "day": clean_int(row.get("day")),
        },
        "incident_type": row.get("incident_type") or None,
        "country": row.get("country") or None,
        "region": row.get("area") or None,
        "location": location,
        "activity": row.get("activity") or None,
        "sex": row.get("sex") or None,
        "age": row.get("age") or None,
        "injury_summary": row.get("injury_summary") or None,
        "fatal": bool(clean_int(row.get("fatal"))),
        "species": {
            "common": row.get("species_common") or None,
            "scientific": row.get("species_scientific") or None,
        },
        "source": {
            "name": row.get("source_name") or None,
            "path": row.get("source_path") or None,
            "row_number": clean_int(row.get("source_row_number")),
            "source_record_id": row.get("source_record_id") or None,
        },
        "duplicate": {
            "is_duplicate": bool(clean_int(row.get("is_duplicate"))),
            "duplicate_of": row.get("duplicate_of") or None,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def bulk_replace(collection, documents: list[dict[str, Any]], dry_run: bool) -> int:
    if dry_run or not documents:
        return len(documents)
    result = collection.bulk_write([ReplaceOne({"_id": doc["_id"]}, doc, upsert=True) for doc in documents], ordered=False)
    return result.upserted_count + result.modified_count


def build_sources(inventory: list[dict[str, Any]], source_counts: Counter) -> list[dict[str, Any]]:
    documents = []
    for item in inventory:
        name = item.get("source_name")
        if not name:
            continue
        documents.append(
            {
                "_id": name,
                "name": name,
                "visibility": "public",
                "source_url": item.get("source_url"),
                "path": item.get("path"),
                "rows_raw": item.get("rows_raw", 0),
                "rows_normalized": item.get("rows_normalized", 0),
                "records_loaded": source_counts.get(name, 0),
            }
        )
    return documents


def build_species(incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for incident in incidents:
        common = incident["species"].get("common")
        if not common:
            continue
        bucket = buckets.setdefault(
            common,
            {"_id": common, "common": common, "scientific_names": set(), "visibility": "public", "incident_count": 0},
        )
        bucket["incident_count"] += 1
        scientific = incident["species"].get("scientific")
        if scientific:
            bucket["scientific_names"].add(scientific)
    return [{**doc, "scientific_names": sorted(doc["scientific_names"])} for doc in buckets.values()]


def build_locations(incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for incident in incidents:
        location_name = incident["location"].get("name")
        country = incident.get("country")
        region = incident.get("region")
        if not any([location_name, country, region]):
            continue
        key = "|".join(str(value or "") for value in [country, region, location_name])
        bucket = buckets.setdefault(
            key,
            {
                "_id": key,
                "visibility": "public",
                "country": country,
                "region": region,
                "name": location_name,
                "incident_count": 0,
            },
        )
        if incident["location"].get("geo") and not bucket.get("geo"):
            bucket["geo"] = incident["location"]["geo"]
        bucket["incident_count"] += 1
    return list(buckets.values())


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Seed MongoDB Atlas collections for the API schema.")
    parser.add_argument("--jsonl", type=Path, default=Path("data/processed/complete_incidents_scrubbed.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("reports/source_comparison_summary.json"))
    parser.add_argument("--inventory", type=Path, default=Path("reports/source_inventory.json"))
    parser.add_argument("--database", default=os.getenv("MONGODB_DATABASE", "AI1SAD"))
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is required")

    source_rows = read_jsonl(args.jsonl)
    incidents = [incident_document(row) for row in source_rows]
    source_counts = Counter(incident["source"]["name"] for incident in incidents)
    summary = json.loads(args.summary.read_text(encoding="utf-8")) if args.summary.exists() else {}
    inventory = json.loads(args.inventory.read_text(encoding="utf-8")) if args.inventory.exists() else []

    sources = build_sources(inventory, source_counts)
    species = build_species(incidents)
    locations = build_locations(incidents)
    now = datetime.now(timezone.utc).isoformat()
    ingestion_run = {
        "_id": f"seed_{now}",
        "visibility": "internal",
        "started_at": now,
        "completed_at": now,
        "records_seen": len(source_rows),
        "records_loaded": len(incidents),
        "source_count": len(sources),
    }
    quality_report = {
        "_id": "latest_data_quality_report",
        "visibility": "internal",
        "created_at": now,
        "summary": summary,
    }
    private_note_placeholder = {
        "_id": "schema_placeholder",
        "visibility": "private",
        "incident_id": None,
        "note": "Private notes are never exposed by public API routes.",
        "created_at": now,
    }

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    db = client[args.database]
    if args.replace and not args.dry_run:
        for collection in COLLECTIONS.values():
            db[collection].drop()

    counts = {
        "incidents": bulk_replace(db[COLLECTIONS["incidents"]], incidents, args.dry_run),
        "sources": bulk_replace(db[COLLECTIONS["sources"]], sources, args.dry_run),
        "species": bulk_replace(db[COLLECTIONS["species"]], species, args.dry_run),
        "locations": bulk_replace(db[COLLECTIONS["locations"]], locations, args.dry_run),
        "ingestion_runs": bulk_replace(db[COLLECTIONS["ingestion_runs"]], [ingestion_run], args.dry_run),
        "data_quality_reports": bulk_replace(db[COLLECTIONS["data_quality_reports"]], [quality_report], args.dry_run),
        "private_notes": bulk_replace(db[COLLECTIONS["private_notes"]], [private_note_placeholder], args.dry_run),
    }
    if not args.dry_run:
        ensure_mongodb_indexes(db)

    print(json.dumps({"database": args.database, "dry_run": args.dry_run, "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
