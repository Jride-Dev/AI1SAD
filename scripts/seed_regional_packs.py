from __future__ import annotations

from app.mongodb import COLLECTIONS, ensure_mongodb_indexes, get_database
from app.services.regional_packs import INITIAL_REGIONAL_PACKS


def main() -> None:
    db = get_database()
    ensure_mongodb_indexes(db)
    collection = db[COLLECTIONS["regional_packs"]]
    for pack in INITIAL_REGIONAL_PACKS:
        collection.replace_one({"pack_id": pack["pack_id"]}, pack, upsert=True)
    print(f"Seeded {len(INITIAL_REGIONAL_PACKS)} regional packs.")


if __name__ == "__main__":
    main()
