from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Iterable


SOURCE_COLUMNS = {
    "case_number": "Case Number",
    "date": "Date",
    "year": "Year",
    "type": "Type",
    "country": "Country",
    "area": "Area",
    "location": "Location",
    "activity": "Activity",
    "sex": "Sex ",
    "age": "Age",
    "injury": "Injury",
    "fatal": "Fatal (Y/N)",
    "time": "Time",
    "species": "Species ",
}

PUBLIC_COLUMNS = [
    "incident_id",
    "case_number_public",
    "date_text",
    "year",
    "incident_type",
    "country_normalized",
    "area_normalized",
    "location_public",
    "activity_normalized",
    "sex",
    "age",
    "injury_summary",
    "fatal",
    "time_text",
    "species_normalized",
]

ADDRESS_PATTERNS = [
    re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.' -]+\s+(street|st\.?|road|rd\.?|avenue|ave\.?|drive|dr\.?|lane|ln\.?|boulevard|blvd\.?)\b", re.I),
    re.compile(r"\b(?:near|off|at)\s+\d{1,6}\b", re.I),
]


def clean_text(value: object) -> str | None:
    text = "" if value is None else str(value)
    text = text.replace("\ufffd", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def normalize_country(value: object) -> str | None:
    text = clean_text(value)
    return text.upper() if text else None


def normalize_label(value: object) -> str | None:
    text = clean_text(value)
    return text.lower() if text else None


def parse_int(value: object) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d{1,4}", text)
    return int(match.group(0)) if match else None


def parse_fatal(value: object) -> int:
    text = (clean_text(value) or "").upper()
    return 1 if text.startswith("Y") else 0


def public_case_number(value: object) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    return re.sub(r"[^0-9A-Za-z.-]", "", text)[:32]


def make_incident_id(row: dict[str, str]) -> str:
    raw = "|".join(clean_text(row.get(SOURCE_COLUMNS[key])) or "" for key in ["case_number", "date", "year", "country", "area", "activity"])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def public_location(value: object) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    for pattern in ADDRESS_PATTERNS:
        text = pattern.sub("[redacted address]", text)
    parts = [part.strip() for part in re.split(r"[,;/]", text) if part.strip()]
    if len(parts) > 2:
        parts = parts[:2]
    return ", ".join(parts)[:160] or None


def injury_summary(value: object) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[name redacted]", text)
    return text[:240]


def normalize_row(row: dict[str, str]) -> dict[str, object] | None:
    year = parse_int(row.get(SOURCE_COLUMNS["year"]))
    case_number = public_case_number(row.get(SOURCE_COLUMNS["case_number"]))
    if not case_number and year is None:
        return None
    return {
        "incident_id": make_incident_id(row),
        "case_number_public": case_number,
        "date_text": clean_text(row.get(SOURCE_COLUMNS["date"])),
        "year": year,
        "incident_type": clean_text(row.get(SOURCE_COLUMNS["type"])),
        "country_normalized": normalize_country(row.get(SOURCE_COLUMNS["country"])),
        "area_normalized": clean_text(row.get(SOURCE_COLUMNS["area"])),
        "location_public": public_location(row.get(SOURCE_COLUMNS["location"])),
        "activity_normalized": normalize_label(row.get(SOURCE_COLUMNS["activity"])),
        "sex": clean_text(row.get(SOURCE_COLUMNS["sex"])),
        "age": clean_text(row.get(SOURCE_COLUMNS["age"])),
        "injury_summary": injury_summary(row.get(SOURCE_COLUMNS["injury"])),
        "fatal": parse_fatal(row.get(SOURCE_COLUMNS["fatal"])),
        "time_text": clean_text(row.get(SOURCE_COLUMNS["time"])),
        "species_normalized": normalize_label(row.get(SOURCE_COLUMNS["species"])),
    }


def read_source_csv(path: Path) -> Iterable[dict[str, str]]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                rows = list(csv.DictReader(handle))
                yield from rows
            return
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode {path}")


def normalize_file(path: Path) -> list[dict[str, object]]:
    seen: set[str] = set()
    normalized: list[dict[str, object]] = []
    for row in read_source_csv(path):
        record = normalize_row(row)
        if not record:
            continue
        incident_id = str(record["incident_id"])
        if incident_id in seen:
            continue
        seen.add(incident_id)
        normalized.append(record)
    return normalized
