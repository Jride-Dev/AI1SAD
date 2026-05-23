from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo import MongoClient, ReplaceOne
from pymongo.collection import Collection


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def clean_document(document: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in document.items():
        if value == "":
            cleaned[key] = None
        else:
            cleaned[key] = value
    for int_key in ["year", "month", "day", "fatal", "is_duplicate", "source_row_number"]:
        if cleaned.get(int_key) is not None:
            cleaned[int_key] = int(float(cleaned[int_key]))
    for float_key in ["latitude", "longitude"]:
        if cleaned.get(float_key) is not None:
            cleaned[float_key] = float(cleaned[float_key])
    cleaned["_id"] = cleaned["record_id"]
    return cleaned


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                documents.append(clean_document(json.loads(line)))
    return documents


def replace_many(collection: Collection, documents: list[dict[str, Any]], dry_run: bool) -> int:
    if dry_run:
        return len(documents)
    if not documents:
        return 0
    operations = [ReplaceOne({"_id": document["_id"]}, document, upsert=True) for document in documents]
    result = collection.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count


def ensure_indexes(collection: Collection, dry_run: bool) -> None:
    if dry_run:
        return
    collection.create_index("canonical_key")
    collection.create_index("source_name")
    collection.create_index("year")
    collection.create_index("country")
    collection.create_index("is_duplicate")
    collection.create_index([("country", 1), ("year", -1)])
    collection.create_index([("latitude", 1), ("longitude", 1)])


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Load scrubbed shark incident records into MongoDB.")
    parser.add_argument("--jsonl", type=Path, default=Path("data/processed/complete_incidents_scrubbed.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("reports/source_comparison_summary.json"))
    parser.add_argument("--inventory", type=Path, default=Path("reports/source_inventory.json"))
    parser.add_argument("--database", default=os.getenv("MONGODB_DATABASE", "AI1SAD"))
    parser.add_argument("--incidents-collection", default="incidents_scrubbed")
    parser.add_argument("--metadata-collection", default="dataset_builds")
    parser.add_argument("--replace-collection", action="store_true", help="Drop the incidents collection before loading.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is required. Put it in .env or set it in the environment.")

    documents = read_jsonl(args.jsonl)
    summary = json.loads(args.summary.read_text(encoding="utf-8")) if args.summary.exists() else {}
    inventory = json.loads(args.inventory.read_text(encoding="utf-8")) if args.inventory.exists() else []

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    database = client[args.database]
    incidents = database[args.incidents_collection]
    metadata = database[args.metadata_collection]

    if args.replace_collection and not args.dry_run:
        incidents.drop()
    changed = replace_many(incidents, documents, args.dry_run)
    ensure_indexes(incidents, args.dry_run)

    build_doc = {
        "_id": "latest_scrubbed_build",
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "incidents_collection": args.incidents_collection,
        "record_count": len(documents),
        "summary": summary,
        "source_inventory": inventory,
        "privacy": {
            "victim_names_included": False,
            "source_notes_included": False,
            "pdf_or_href_links_included": False,
        },
    }
    if not args.dry_run:
        metadata.replace_one({"_id": build_doc["_id"]}, build_doc, upsert=True)

    print(json.dumps({
        "database": args.database,
        "incidents_collection": args.incidents_collection,
        "metadata_collection": args.metadata_collection,
        "records_seen": len(documents),
        "records_changed_or_upserted": changed,
        "dry_run": args.dry_run,
    }, indent=2))


if __name__ == "__main__":
    main()
