from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from clean_normalize import PUBLIC_COLUMNS, normalize_file


CREATE_SQL = """
DROP TABLE IF EXISTS public_incidents;
CREATE TABLE public_incidents (
    incident_id TEXT PRIMARY KEY,
    case_number_public TEXT,
    date_text TEXT,
    year INTEGER,
    incident_type TEXT,
    country_normalized TEXT,
    area_normalized TEXT,
    location_public TEXT,
    activity_normalized TEXT,
    sex TEXT,
    age TEXT,
    injury_summary TEXT,
    fatal INTEGER NOT NULL CHECK (fatal IN (0, 1)),
    time_text TEXT,
    species_normalized TEXT
);
CREATE INDEX IF NOT EXISTS idx_public_incidents_year ON public_incidents(year);
CREATE INDEX IF NOT EXISTS idx_public_incidents_country ON public_incidents(country_normalized);
CREATE INDEX IF NOT EXISTS idx_public_incidents_activity ON public_incidents(activity_normalized);
CREATE INDEX IF NOT EXISTS idx_public_incidents_species ON public_incidents(species_normalized);
"""


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(CREATE_SQL)
        conn.executemany(
            f"INSERT INTO public_incidents ({', '.join(PUBLIC_COLUMNS)}) VALUES ({', '.join('?' for _ in PUBLIC_COLUMNS)})",
            [[row.get(column) for column in PUBLIC_COLUMNS] for row in rows],
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize public shark attack records and export CSV/SQLite.")
    parser.add_argument("--source", type=Path, default=Path("data/raw/attacks.csv"))
    parser.add_argument("--csv", type=Path, default=Path("data/public/incidents_public.csv"))
    parser.add_argument("--sqlite", type=Path, default=Path("data/public/shark_attacks.sqlite"))
    args = parser.parse_args()
    rows = normalize_file(args.source)
    write_csv(args.csv, rows)
    write_sqlite(args.sqlite, rows)
    print(f"Exported {len(rows)} public records")
    print(f"CSV: {args.csv}")
    print(f"SQLite: {args.sqlite}")


if __name__ == "__main__":
    main()

