from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


PUBLIC_COLUMNS = [
    "record_id",
    "canonical_key",
    "source_name",
    "source_path",
    "source_row_number",
    "source_record_id",
    "date_text",
    "year",
    "month",
    "day",
    "incident_type",
    "country",
    "area",
    "location_public",
    "activity",
    "sex",
    "age",
    "injury_summary",
    "fatal",
    "species_common",
    "species_scientific",
    "latitude",
    "longitude",
    "is_duplicate",
    "duplicate_of",
]

PRIVATE_OR_RESTRICTED_COLUMNS = {
    "name",
    "investigator or source",
    "source",
    "pdf",
    "href formula",
    "href",
}

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

SOURCE_URLS = {
    "local_legacy_attacks_csv": "local:data/raw/attacks.csv",
    "gsaf_latest_xls": "https://www.sharkattackfile.net/spreadsheets/GSAF5.xls",
    "github_n_enzer_attacks_csv": "https://github.com/N-Enzer/SharkAttackAnalysis",
    "github_ordovas_attacks_csv": "https://github.com/ordovas/pandas-project",
    "github_ordovas_clean_csv": "https://github.com/ordovas/pandas-project",
    "australian_shark_incident_database": "https://github.com/cjabradshaw/AustralianSharkIncidentDatabase",
    "kaggle_teajay_global_shark_attacks": "https://www.kaggle.com/datasets/teajay/global-shark-attacks/data",
}


@dataclass(frozen=True)
class SourceSpec:
    name: str
    path: Path
    kind: str
    country_default: str | None = None


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def clean_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).replace("\ufffd", "").replace("\xca", "").strip()
    text = re.sub(r"\s+", " ", text)
    if not text or text.lower() in {"nan", "none", "null", "unknown"}:
        return None
    return text


def clean_label(value: Any) -> str | None:
    text = clean_text(value)
    return text.lower() if text else None


def parse_int(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"-?\d{1,4}", text)
    return int(match.group(0)) if match else None


def parse_year(value: Any) -> int | None:
    year = parse_int(value)
    if year is None or year < 1500 or year > 2027:
        return None
    return year


def parse_float(value: Any) -> float | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_day_month(value: Any) -> tuple[int | None, int | None]:
    if hasattr(value, "day") and hasattr(value, "month"):
        try:
            return int(value.day), int(value.month)
        except Exception:
            pass
    text = clean_text(value)
    if not text:
        return None, None
    lower = text.lower()
    month = None
    for label, number in MONTHS.items():
        if re.search(rf"\b{re.escape(label)}\b", lower):
            month = number
            break
    day = None
    day_match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\b", lower)
    if day_match:
        possible_day = int(day_match.group(1))
        if 1 <= possible_day <= 31:
            day = possible_day
    return day, month


def parse_fatal(value: Any, injury_value: Any = None) -> int:
    text = (clean_text(value) or clean_text(injury_value) or "").lower()
    return 1 if text.startswith("y") or text == "fatal" or "fatal" in text else 0


def clean_location(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(
        r"\b\d{1,6}\s+[A-Za-z0-9.' -]+\s+(street|st\.?|road|rd\.?|avenue|ave\.?|drive|dr\.?|lane|ln\.?|boulevard|blvd\.?)\b",
        "[redacted address]",
        text,
        flags=re.I,
    )
    parts = [part.strip() for part in re.split(r"[,;/]", text) if part.strip()]
    return ", ".join(parts[:2])[:160] if parts else text[:160]


def clean_injury(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[name redacted]", text)
    return text[:280]


def row_value(row: pd.Series, *names: str) -> Any:
    lower_map = {str(col).strip().lower(): col for col in row.index}
    for name in names:
        col = lower_map.get(name.strip().lower())
        if col is not None:
            return row.get(col)
    return None


def canonical_key(record: dict[str, Any]) -> str:
    source_id = clean_text(record.get("source_record_id"))
    if source_id and re.search(r"\d", source_id):
        return f"case:{source_id.lower()}"
    keys = dedupe_keys(record)
    if keys:
        return keys[0]
    raw = "|".join("" if value is None else str(value).strip().lower() for value in record.values())
    return "hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def dedupe_keys(record: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    source_id = clean_text(record.get("source_record_id"))
    if source_id and re.search(r"\d", source_id) and not source_id.startswith("asid:"):
        keys.append(f"case:{source_id.lower()}")
    if record.get("year") and record.get("country") and record.get("location_public"):
        fields = [
            record.get("year"),
            record.get("month"),
            record.get("day"),
            record.get("country"),
            record.get("area"),
            record.get("location_public"),
            record.get("activity"),
            record.get("fatal"),
        ]
        raw = "|".join("" if value is None else str(value).strip().lower() for value in fields)
        keys.append("match:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20])
    if keys:
        return keys
    fields = [
        record.get("year"),
        record.get("month"),
        record.get("day"),
        record.get("country"),
        record.get("area"),
        record.get("location_public"),
        record.get("activity"),
        record.get("fatal"),
    ]
    raw = "|".join("" if value is None else str(value).strip().lower() for value in fields)
    return ["hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]]


def record_id(record: dict[str, Any]) -> str:
    raw = "|".join(
        clean_text(record.get(key)) or ""
        for key in ["source_name", "source_row_number", "canonical_key", "source_record_id", "date_text", "location_public"]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def read_frame(spec: SourceSpec) -> pd.DataFrame:
    if not spec.path.exists():
        return pd.DataFrame()
    if spec.path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(spec.path)
    if spec.path.suffix.lower() == ".txt":
        return pd.read_csv(spec.path, sep="\t", encoding="utf-8")
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(spec.path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(spec.path, encoding="latin-1")


def normalize_gsaf_like(spec: SourceSpec, frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row_number, (_, row) in enumerate(frame.iterrows(), start=1):
        year = parse_year(row_value(row, "Year"))
        source_record_id = clean_text(row_value(row, "Case Number", "Case Number.1"))
        date_text = clean_text(row_value(row, "Date"))
        country = clean_text(row_value(row, "Country"))
        location = clean_location(row_value(row, "Location"))
        if not any([year, source_record_id, date_text, country, location]):
            continue
        day, month = parse_day_month(row_value(row, "Date"))
        record = {
            "source_name": spec.name,
            "source_path": display_path(spec.path),
            "source_row_number": row_number,
            "source_record_id": source_record_id,
            "date_text": date_text,
            "year": year,
            "month": month,
            "day": day,
            "incident_type": clean_text(row_value(row, "Type")),
            "country": country.upper() if country else spec.country_default,
            "area": clean_text(row_value(row, "Area", "State")),
            "location_public": location,
            "activity": clean_label(row_value(row, "Activity")),
            "sex": clean_text(row_value(row, "Sex", "Sex ")),
            "age": clean_text(row_value(row, "Age")),
            "injury_summary": clean_injury(row_value(row, "Injury")),
            "fatal": parse_fatal(row_value(row, "Fatal (Y/N)", "Fatal Y/N", "Fatal"), row_value(row, "Injury")),
            "species_common": clean_label(row_value(row, "Species", "Species ")),
            "species_scientific": None,
            "latitude": None,
            "longitude": None,
        }
        record["canonical_key"] = canonical_key(record)
        record["record_id"] = record_id(record)
        records.append(record)
    return records


def normalize_asid(spec: SourceSpec, frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row_number, (index, row) in enumerate(frame.iterrows(), start=1):
        year = parse_year(row_value(row, "Incident.year"))
        location = clean_location(row_value(row, "Location"))
        if not any([year, location]):
            continue
        day = parse_int(row_value(row, "Incident.day"))
        month = parse_int(row_value(row, "Incident.month"))
        record = {
            "source_name": spec.name,
            "source_path": display_path(spec.path),
            "source_row_number": row_number,
            "source_record_id": f"asid:{index + 1}",
            "date_text": "-".join(str(part) for part in [year, month, day] if part),
            "year": year,
            "month": month,
            "day": day,
            "incident_type": clean_text(row_value(row, "Provoked.unprovoked")),
            "country": "AUSTRALIA",
            "area": clean_text(row_value(row, "State")),
            "location_public": location,
            "activity": clean_label(row_value(row, "Victim.activity")),
            "sex": clean_text(row_value(row, "Victim.gender")),
            "age": clean_text(row_value(row, "Victim.age")),
            "injury_summary": clean_injury(
                row_value(row, "Injury.description", "Victim.injury", "Injury.severity", "Injury.severity\xca")
            ),
            "fatal": parse_fatal(row_value(row, "Victim.injury"), row_value(row, "Injury.severity")),
            "species_common": clean_label(row_value(row, "Shark.common.name")),
            "species_scientific": clean_text(row_value(row, "Shark.scientific.name")),
            "latitude": parse_float(row_value(row, "Latitude")),
            "longitude": parse_float(row_value(row, "Longitude")),
        }
        record["canonical_key"] = canonical_key(record)
        record["record_id"] = record_id(record)
        records.append(record)
    return records


def source_specs(root: Path) -> list[SourceSpec]:
    return [
        SourceSpec("local_legacy_attacks_csv", root / "data/raw/attacks.csv", "gsaf"),
        SourceSpec("gsaf_latest_xls", root / "data/raw/external/gsaf/GSAF5_latest.xls", "gsaf"),
        SourceSpec("github_n_enzer_attacks_csv", root / "data/raw/external/github/SharkAttackAnalysis/attacks.csv", "gsaf"),
        SourceSpec("github_ordovas_attacks_csv", root / "data/raw/external/github/pandas-project/shark-attack/attacks.csv", "gsaf"),
        SourceSpec("github_ordovas_clean_csv", root / "data/raw/external/github/pandas-project/shark-attack/attacks_clean.csv", "gsaf"),
        SourceSpec(
            "australian_shark_incident_database",
            root / "data/raw/external/github/AustralianSharkIncidentDatabase/data/timedb2.txt",
            "asid",
            "AUSTRALIA",
        ),
    ]


def build(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_records: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for spec in source_specs(root):
        frame = read_frame(spec)
        if frame.empty:
            inventory.append({"source_name": spec.name, "path": display_path(spec.path), "exists": spec.path.exists(), "rows_raw": 0, "rows_normalized": 0})
            continue
        if spec.kind == "asid":
            records = normalize_asid(spec, frame)
        else:
            records = normalize_gsaf_like(spec, frame)
        inventory.append(
            {
                "source_name": spec.name,
                "source_url": SOURCE_URLS.get(spec.name),
                "path": display_path(spec.path),
                "exists": spec.path.exists(),
                "rows_raw": int(len(frame)),
                "rows_normalized": len(records),
                "columns": [str(col) for col in frame.columns],
            }
        )
        all_records.extend(records)

    seen: dict[str, str] = {}
    for record in all_records:
        keys = dedupe_keys(record)
        duplicate_of = next((seen[key] for key in keys if key in seen), None)
        record["is_duplicate"] = 1 if duplicate_of else 0
        record["duplicate_of"] = duplicate_of
        if not duplicate_of:
            for key in keys:
                seen[key] = record["record_id"]

    data = pd.DataFrame(all_records)
    if data.empty:
        data = pd.DataFrame(columns=PUBLIC_COLUMNS)
    data = data.reindex(columns=PUBLIC_COLUMNS)
    return data, pd.DataFrame(inventory)


def write_sqlite(path: Path, records: pd.DataFrame, inventory: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    inventory_for_sql = inventory.copy()
    if "columns" in inventory_for_sql.columns:
        inventory_for_sql["columns"] = inventory_for_sql["columns"].apply(
            lambda value: json.dumps(value) if isinstance(value, list) else value
        )
    with sqlite3.connect(path) as conn:
        records.to_sql("incidents_scrubbed", conn, if_exists="replace", index=False)
        inventory_for_sql.to_sql("source_inventory", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_key ON incidents_scrubbed(canonical_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_year ON incidents_scrubbed(year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_country ON incidents_scrubbed(country)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_source ON incidents_scrubbed(source_name)")
        conn.commit()


def write_report(path: Path, records: pd.DataFrame, inventory: pd.DataFrame) -> None:
    unique_records = records[records["is_duplicate"] == 0]
    source_counts = records.groupby("source_name").size().sort_values(ascending=False).to_dict() if not records.empty else {}
    invalid_fatal = int((~records["fatal"].isin([0, 1])).sum()) if not records.empty else 0
    coords = records[records["latitude"].notna() | records["longitude"].notna()] if not records.empty else records
    invalid_coords = 0
    if not coords.empty:
        invalid_coords = int(
            (
                (coords["latitude"].notna() & ~coords["latitude"].between(-90, 90))
                | (coords["longitude"].notna() & ~coords["longitude"].between(-180, 180))
            ).sum()
        )
    year_values = pd.to_numeric(unique_records["year"], errors="coerce") if not unique_records.empty else pd.Series(dtype=float)
    summary = {
        "total_normalized_records": int(len(records)),
        "unique_records_after_dedupe": int(len(unique_records)),
        "duplicate_records": int(records["is_duplicate"].sum()) if not records.empty else 0,
        "sources": source_counts,
        "quality": {
            "min_year": int(year_values.min()) if not year_values.dropna().empty else None,
            "max_year": int(year_values.max()) if not year_values.dropna().empty else None,
            "unique_countries": int(unique_records["country"].dropna().nunique()) if not unique_records.empty else 0,
            "records_missing_year": int(unique_records["year"].isna().sum()) if not unique_records.empty else 0,
            "records_missing_country": int(unique_records["country"].isna().sum()) if not unique_records.empty else 0,
            "records_missing_location": int(unique_records["location_public"].isna().sum()) if not unique_records.empty else 0,
            "invalid_fatal_values": invalid_fatal,
            "records_with_coordinates": int(len(coords)) if not coords.empty else 0,
            "invalid_coordinate_values": invalid_coords,
        },
        "kaggle_status": "Not downloaded automatically: Kaggle CLI is not installed/authenticated. The dataset URL is recorded for manual/API import.",
        "privacy_scrub": {
            "victim_names_published": False,
            "per_case_pdf_or_href_published": False,
            "private_source_notes_published": False,
            "exact_street_addresses_redacted": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (path.parent / "source_inventory.json").write_text(inventory.to_json(orient="records", indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a complete scrubbed multi-source shark incident database.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--report", type=Path, default=Path("reports/source_comparison_summary.json"))
    args = parser.parse_args()

    root = args.root.resolve()
    records, inventory = build(root)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    records.to_csv(out_dir / "complete_incidents_scrubbed.csv", index=False)
    records.to_json(out_dir / "complete_incidents_scrubbed.jsonl", orient="records", lines=True, force_ascii=False)
    write_sqlite(out_dir / "complete_incidents_scrubbed.sqlite", records, inventory)
    write_report(args.report, records, inventory)

    unique_count = int((records["is_duplicate"] == 0).sum()) if not records.empty else 0
    print(f"Normalized records: {len(records)}")
    print(f"Unique records after dedupe: {unique_count}")
    print(f"Outputs: {out_dir}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
