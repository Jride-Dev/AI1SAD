from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient, ReplaceOne

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mongodb import COLLECTIONS, ensure_mongodb_indexes
from app.risk_model import REGIONAL_RISK_PROFILES
from scripts.load_mongodb import load_env


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Seed regional shark encounter warning profiles.")
    parser.add_argument("--database", default=os.getenv("MONGODB_DATABASE", "AI1SAD"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is required")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    db = client[args.database]
    collection = db[COLLECTIONS["regional_risk_profiles"]]
    if not args.dry_run:
        collection.bulk_write(
            [ReplaceOne({"_id": profile["_id"]}, profile, upsert=True) for profile in REGIONAL_RISK_PROFILES],
            ordered=False,
        )
        ensure_mongodb_indexes(db)

    print(json.dumps({"database": args.database, "profiles": len(REGIONAL_RISK_PROFILES), "dry_run": args.dry_run}, indent=2))


if __name__ == "__main__":
    main()

