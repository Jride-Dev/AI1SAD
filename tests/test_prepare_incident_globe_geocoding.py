from __future__ import annotations

import csv
from pathlib import Path

from scripts.prepare_incident_globe_geocoding import prepare, prepare_database


def test_prepare_deduplicates_context_without_private_fields(tmp_path: Path):
    input_path = tmp_path / "review.csv"
    output_path = tmp_path / "upload.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["location", "region", "country", "date_text", "source_record_ids"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "location": "Chatham Island",
                "region": "Massachusetts",
                "country": "USA",
                "date_text": "21-Jul-01",
                "source_record_ids": "private-source-id",
            }
        )
        writer.writerow(
            {
                "location": " Chatham  Island ",
                "region": "Massachusetts",
                "country": "USA",
                "date_text": "another date",
                "source_record_ids": "another-private-source-id",
            }
        )

    summary = prepare(input_path, output_path)
    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8-sig", newline="")))

    assert summary == {"incident_records": 2, "unique_context_queries": 1, "batches": 1}
    assert len(rows) == 1
    assert rows[0]["address"] == "Chatham Island, Massachusetts, USA"
    assert rows[0]["incident_count"] == "2"
    assert "date_text" not in rows[0]
    assert "source_record_ids" not in rows[0]


def test_prepare_database_filters_invalid_and_blank_locations(tmp_path: Path):
    database_path = tmp_path / "incidents.sqlite"
    output_path = tmp_path / "upload.csv"
    import sqlite3

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE incidents_scrubbed (
                year INTEGER, location_public TEXT, area TEXT, country TEXT,
                latitude REAL, longitude REAL, incident_type TEXT, species_common TEXT
            )"""
        )
        connection.executemany(
            "INSERT INTO incidents_scrubbed VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1950, "Bondi Beach", "New South Wales", "Australia", None, None, "Unprovoked", None),
                (1951, "Bondi Beach", "New South Wales", "Australia", None, None, "Unprovoked", None),
                (1952, "", "Queensland", "Australia", None, None, "Unprovoked", None),
                (1953, "Fake Beach", "Florida", "USA", None, None, "Invalid", None),
                (1954, "Known Point", "Florida", "USA", 1.0, 2.0, "Unprovoked", None),
            ],
        )

    summary = prepare_database(database_path, output_path, 1900, 2026)
    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8-sig", newline="")))

    assert summary == {"incident_records": 3, "unique_context_queries": 1, "batches": 0}
    assert rows[0]["address"] == "Bondi Beach, New South Wales, Australia"
    assert rows[0]["incident_count"] == "2"
