from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sqlite3
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path("data/review/incident_globe_all_geocode_review_2026-10-03.csv")
DEFAULT_OUTPUT = Path("data/review/incident_globe_csv2geo_upload_2026-10-03.csv")
DEFAULT_DATABASE = Path("data/processed/complete_incidents_scrubbed.sqlite")


def clean(value: str | None) -> str:
    return " ".join((value or "").split())


def write_queries(counts: Counter[tuple[str, str, str]], output_path: Path, batch_size: int) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = ["query_id", "address", "location", "region", "country", "incident_count"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        ordered_keys = sorted(counts, key=lambda item: (-counts[item], item[2], item[1], item[0]))
        for location, region, country in ordered_keys:
            context = ", ".join(part for part in (location, region, country) if part)
            query_id = hashlib.sha256("|".join((location, region, country)).encode("utf-8")).hexdigest()[:16]
            writer.writerow(
                {
                    "query_id": query_id,
                    "address": context,
                    "location": location,
                    "region": region,
                    "country": country,
                    "incident_count": counts[(location, region, country)],
                }
            )

    if batch_size > 0:
        with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
            prepared_rows = list(csv.DictReader(handle))
        for index in range(0, len(prepared_rows), batch_size):
            batch_path = output_path.with_name(
                f"{output_path.stem}_batch_{index // batch_size + 1:02d}{output_path.suffix}"
            )
            with batch_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=prepared_rows[0].keys())
                writer.writeheader()
                writer.writerows(prepared_rows[index : index + batch_size])

    return math.ceil(len(counts) / batch_size) if batch_size > 0 else 0


def prepare(input_path: Path, output_path: Path, batch_size: int = 100) -> dict[str, int]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    keys = [
        (clean(row.get("location")), clean(row.get("region")), clean(row.get("country")))
        for row in rows
    ]
    counts = Counter(keys)
    batches = write_queries(counts, output_path, batch_size)
    return {"incident_records": len(rows), "unique_context_queries": len(counts), "batches": batches}


def prepare_database(
    database_path: Path,
    output_path: Path,
    start_year: int,
    end_year: int,
    batch_size: int = 0,
) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT location_public, area, country
            FROM incidents_scrubbed
            WHERE year BETWEEN ? AND ?
              AND (latitude IS NULL OR longitude IS NULL)
              AND lower(trim(coalesce(incident_type, ''))) != 'invalid'
              AND lower(trim(coalesce(species_common, ''))) NOT IN ('no shark involvement', 'not a shark')
            """,
            (start_year, end_year),
        ).fetchall()

    keys = [
        (clean(location), clean(region), clean(country))
        for location, region, country in rows
        if clean(location)
    ]
    counts = Counter(keys)
    batches = write_queries(counts, output_path, batch_size)
    return {"incident_records": len(rows), "unique_context_queries": len(counts), "batches": batches}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a public-safe, context-rich CSV2GEO batch from the Incident Globe review queue."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--start-year", type=int, default=1900)
    parser.add_argument("--end-year", type=int, default=2026)
    args = parser.parse_args()
    if args.database:
        summary = prepare_database(args.database, args.output, args.start_year, args.end_year, args.batch_size)
    else:
        summary = prepare(args.input, args.output, args.batch_size)
    print(f"Prepared {summary['unique_context_queries']} contextual queries for {summary['incident_records']} records.")
    print(f"Created {summary['batches']} batch files with at most {args.batch_size} rows each.")
    print(args.output)


if __name__ == "__main__":
    main()
