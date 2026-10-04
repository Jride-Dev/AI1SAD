from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi import HTTPException

from app import api_v1
from app.services.incident_globe import (
    build_globe_dataset,
    coordinate_matches_country,
    coordinates_for_record,
    explicitly_invalid,
    outcome_category,
    provocation_label,
)


COLUMNS = [
    "record_id", "canonical_key", "source_name", "source_path", "source_row_number", "source_record_id",
    "date_text", "year", "month", "day", "incident_type", "country", "area", "location_public",
    "activity", "sex", "age", "injury_summary", "fatal", "species_common", "species_scientific",
    "latitude", "longitude", "is_duplicate", "duplicate_of",
]


def create_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(f"CREATE TABLE incidents_scrubbed ({', '.join(f'{column} TEXT' for column in COLUMNS)})")
        rows = [
            ["base-1", "case:one", "gsaf_latest_xls", "gsaf.xls", 10, "2005.01.02", "2-Jan-2005", 2005, 1, 2, "Unprovoked", "USA", "Florida", "Example Beach", "surfing", "M", "30", "Leg injury", 0, "bull shark", None, None, None, 0, None],
            ["dup-1", "case:one", "github_ordovas_attacks_csv", "mirror.csv", 20, "2005.01.02", "2-Jan-2005", 2005, 1, 2, "Unprovoked", "USA", "Florida", "Example Beach", "surfing", "M", "30", "Leg injury", 0, "bull shark", None, None, None, 1, "base-1"],
            ["base-2", "case:two", "local_legacy_attacks_csv", "attacks.csv", 30, "2014.03.04", "4-Mar-2014", 2014, 3, 4, "Provoked", "AUSTRALIA", "WA", "Mapped Beach", "fishing", "M", "40", "No injury", 0, None, None, -31.0, 115.0, 0, None],
        ]
        connection.executemany(f"INSERT INTO incidents_scrubbed VALUES ({','.join('?' for _ in COLUMNS)})", rows)


def create_geocodes(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Location", "Latitude", "Longitude", "ReviewStatus"])
        writer.writeheader()
        writer.writerow({"Location": "Example Beach", "Latitude": 27.5, "Longitude": -80.2, "ReviewStatus": "reviewed"})


def create_context_geocodes(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["location", "region", "country", "latitude", "longitude", "relevance", "validation_status"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "location": "Chatham Island",
                "region": "Massachusetts",
                "country": "USA",
                "latitude": 41.68227,
                "longitude": -70.0146,
                "relevance": 0.98,
                "validation_status": "validated",
            }
        )


def create_hal(path: Path) -> None:
    payload = {
        "records": [
            {
                "source_record_id": "sharks_happen:0100", "source_row_number": 103, "year": 2005,
                "fatality_claim": False, "consumption_attempt_claim": None, "injury_raw": "Leg injury",
                "duplicate_review": {"status": "exact_candidate", "cross_source_candidates": [{"candidate_record_id": "base-1"}]},
            },
            {
                "source_record_id": "sharks_happen:0101", "source_row_number": 104, "year": 2020,
                "month": 5, "day": 6, "incident_date_raw": "2020-05-06", "country_normalized": "USA",
                "location_raw": "Example Beach", "area_raw": "Florida", "activity_raw": "Swimming",
                "injury_raw": "No injury", "fatality_claim": None, "shark_label_raw": "Tiger",
                "duplicate_review": {"status": "unmatched", "cross_source_candidates": []},
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_globe_dataset_deduplicates_sources_and_keeps_hal_standalone(tmp_path: Path):
    database = tmp_path / "incidents.sqlite"
    geocodes = tmp_path / "geocodes.csv"
    hal = tmp_path / "hal.json"
    create_database(database)
    create_geocodes(geocodes)
    create_hal(hal)

    payload = build_globe_dataset(
        database_path=database,
        geocode_cache_path=geocodes,
        context_geocode_path=tmp_path / "missing-context.csv",
        hal_staging_path=hal,
        generated_at="2026-10-02T00:00:00+00:00",
    )

    assert payload["summary"]["total_records"] == 3
    assert payload["summary"]["mapped_records"] == 3
    assert payload["summary"]["hal_exact_matches_attached"] == 1
    assert payload["summary"]["hal_standalone_records"] == 1
    base = next(record for record in payload["records"] if record["canonical_record_id"] == "base-1")
    assert base["source_count"] == 3
    assert base["provocation"] == "unprovoked"
    assert base["coordinates"]["coordinates"] == [-80.2, 27.5]
    standalone = next(record for record in payload["records"] if record["canonical_record_id"] is None)
    assert standalone["outcome_category"] == "no_injury"
    assert standalone["provocation"] == "unknown"


def test_outcome_and_provocation_are_conservative():
    assert outcome_category(True, "Fatal injuries", []) == "fatal"
    assert outcome_category(False, "No injury to occupant", []) == "no_injury"
    assert outcome_category(False, None, []) == "non_fatal"
    assert provocation_label(["Provoked", "Unprovoked"])[0] == "conflicted"
    assert provocation_label(["Questionable"])[0] == "unknown"
    assert explicitly_invalid({"incident_type": "Invalid", "species_common": "no shark involvement"}) is True
    assert explicitly_invalid({"incident_type": "Questionable", "species_common": None}) is False


def test_approximate_cache_coordinate_must_match_known_country():
    geocodes = {"lighthouse beach": (40.6290808, -73.2211281, True)}

    coordinates, source, confidence = coordinates_for_record(
        {"country": "AUSTRALIA", "location_public": "Lighthouse Beach"},
        geocodes,
    )

    assert coordinates is None
    assert source == "country_mismatch_rejected"
    assert confidence == "unknown"
    assert coordinate_matches_country(-31.9, 115.8, "AUSTRALIA") is True
    assert coordinate_matches_country(40.6, -73.2, "AUSTRALIA") is False
    assert coordinate_matches_country(41.68, -69.96, "USA") is True
    assert coordinate_matches_country(-43.912705, -176.475029, "USA") is False


def test_unreviewed_cache_coordinate_is_never_plotted():
    coordinates, source, confidence = coordinates_for_record(
        {"country": "USA", "location_public": "Chatham Island"},
        {"chatham island": (-43.912705, -176.475029, False)},
    )

    assert coordinates is None
    assert source == "unreviewed_geocode_rejected"
    assert confidence == "unknown"


def test_contextual_geocode_uses_location_region_and_country(tmp_path: Path):
    path = tmp_path / "context.csv"
    create_context_geocodes(path)
    from app.services.incident_globe import load_context_geocodes

    context = load_context_geocodes(path)
    coordinates, source, confidence = coordinates_for_record(
        {"country": "USA", "area": "Massachusetts", "location_public": "Chatham Island"},
        {},
        context,
    )

    assert coordinates == {"type": "Point", "coordinates": [-70.0146, 41.68227]}
    assert source == "csv2geo_contextual"
    assert confidence == "high_contextual"


def test_globe_endpoint_filters_decade_provocation_and_outcome(monkeypatch: pytest.MonkeyPatch):
    records = [
        {"record_id": "a", "decade": 2000, "provocation": "unprovoked", "outcome_category": "fatal", "mapped": True},
        {"record_id": "b", "decade": 2020, "provocation": "provoked", "outcome_category": "no_injury", "mapped": False},
        {"record_id": "c", "decade": 2020, "provocation": "unprovoked", "outcome_category": "non_fatal", "mapped": True},
    ]
    dataset = {
        "schema_version": "incident_globe_v1",
        "generated_at": "2026-10-02T00:00:00+00:00",
        "range": {"start_year": 2000, "end_year": 2026},
        "summary": {
            "total_records": 3,
            "country_mismatch_coordinates_rejected": 2,
            "unreviewed_geocode_coordinates_rejected": 7,
            "contextual_geocode_coordinates_mapped": 11,
        },
        "data_boundaries": {"coordinates_are_not_inferred": True},
    }
    monkeypatch.setattr(api_v1, "_incident_globe_records", lambda: (records, dataset))

    payload = api_v1.incident_globe(decade=2020, provocation="unprovoked", outcome="non_fatal")

    assert [record["record_id"] for record in payload["records"]] == ["c"]
    assert payload["filters"] == {"decade": 2020, "provocation": "unprovoked", "outcome": "non_fatal"}
    assert payload["summary"]["mapped_records"] == 1
    assert payload["summary"]["dataset_total_records"] == 3
    assert payload["summary"]["dataset_country_mismatch_coordinates_rejected"] == 2
    assert payload["summary"]["dataset_unreviewed_geocode_coordinates_rejected"] == 7
    assert payload["summary"]["dataset_contextual_geocode_coordinates_mapped"] == 11


def test_globe_endpoint_rejects_unsupported_filters(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(api_v1, "_incident_globe_records", lambda: ([], {}))

    with pytest.raises(HTTPException) as error:
        api_v1.incident_globe(decade=1990, provocation="all", outcome="all")
    assert error.value.status_code == 422

    with pytest.raises(HTTPException):
        api_v1.incident_globe(decade=None, provocation="mistaken_identity", outcome="all")
