from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_NAME = "GSAF"
SCHEMA_VERSION = 1

SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
DEFAULT_STAGING_PATH = Path("data/imports/gsaf/staging/latest_staging.json")
DEFAULT_REPORT_PATH = Path("data/imports/gsaf/reports/latest_import_report.json")
DEFAULT_BASELINE_PATH = Path("data/imports/gsaf/staging/gsaf_baseline_fingerprints.json")

SIDE_EFFECTS = {
    "creates_warnings": False,
    "creates_alerts": False,
    "creates_public_feed_entries": False,
    "creates_replay_facts": False,
    "creates_drone_observations": False,
    "alters_scoring": False,
    "alters_replay": False,
}

FIELD_ALIASES = {
    "source_case_number": {"case number", "case no", "case", "case id", "case number 1"},
    "source_date_raw": {"date", "incident date"},
    "year": {"year"},
    "country": {"country"},
    "area": {"area", "state", "province", "region"},
    "location": {"location", "site", "beach"},
    "activity": {"activity"},
    "sex": {"sex", "gender"},
    "age": {"age"},
    "injury": {"injury", "injury summary"},
    "fatal_y_n": {"fatal y n", "fatal yn", "fatal", "fatality", "fatal y/n"},
    "time_raw": {"time", "time raw"},
    "species_raw": {"species", "species name", "species involved"},
    "investigator_or_source_raw": {
        "source",
        "investigator or source",
        "investigator source",
        "original source",
    },
    "pdf_case_link_raw": {"pdf", "pdf case link", "case pdf", "case link", "href", "href formula", "url"},
    "original_type_raw": {"type", "original type", "incident type"},
}

SOURCE_FIELDS = [
    "source_case_number",
    "source_date_raw",
    "year",
    "country",
    "area",
    "location",
    "activity",
    "sex",
    "age",
    "injury",
    "fatal_y_n",
    "time_raw",
    "species_raw",
    "investigator_or_source_raw",
    "pdf_case_link_raw",
    "original_type_raw",
]

FINGERPRINT_FIELDS = [
    "source_case_number",
    "source_date_raw",
    "date_normalized",
    "year",
    "country",
    "area",
    "location",
    "activity",
    "sex",
    "age",
    "injury",
    "fatal_y_n",
    "time_raw",
    "species_raw",
    "investigator_or_source_raw",
    "pdf_case_link_raw",
    "original_type_raw",
]

PRECISE_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y.%m.%d %H:%M:%S",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%B %d %Y",
    "%d-%b-%Y",
    "%d-%B-%Y",
]

VAGUE_DATE_MARKERS = {
    "reported",
    "before",
    "after",
    "between",
    "circa",
    "ca.",
    "ca ",
    "early",
    "mid",
    "late",
    "summer",
    "winter",
    "spring",
    "autumn",
    "fall",
    "unknown",
    "possibly",
    "prior to",
}

QUESTIONABLE_MARKERS = {
    "questionable",
    "unconfirmed",
    "unverified",
    "invalid",
    "doubtful",
    "hoax",
    "not confirmed",
}

BEHAVIOR_CANDIDATES = {
    "attempted_predation_event",
    "territorial_displacement",
    "accidental_contact",
    "predatory_probe",
    "competitive_food_response",
    "scavenging_context",
    "mistaken_identity_candidate",
    "unknown_insufficient_evidence",
    "object_contact_or_investigative_bite",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.hour == value.minute == value.second == value.microsecond == 0:
            return value.date().isoformat()
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if value.is_integer():
            return str(int(value))
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def header_key(value: Any) -> str:
    key = clean_cell(value).lower()
    key = re.sub(r"[^a-z0-9]+", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    return re.sub(r"\s+\d+$", "", key)


def raw_value(row: dict[str, Any], field: str) -> str:
    aliases = FIELD_ALIASES[field]
    for header, value in row.items():
        if header_key(header) in aliases:
            return clean_cell(value)
    return ""


def read_tabular_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported GSAF input format: {suffix}")
    if suffix == ".csv":
        return read_csv_rows(path)
    return read_excel_rows(path)


def read_csv_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return [(index, dict(row)) for index, row in enumerate(reader, start=2)]
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"Could not decode CSV file {path}") from last_error


def read_excel_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment-specific guard
        raise RuntimeError("Excel import requires pandas, which is already listed in requirements.txt.") from exc

    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    try:
        frame = pd.read_excel(path, dtype=object, keep_default_na=False, engine=engine)
    except ImportError as exc:  # pragma: no cover - environment-specific guard
        dependency = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
        raise RuntimeError(
            f"Reading {path.suffix.lower()} requires {dependency}; it is declared in requirements.txt but is not installed."
        ) from exc
    return [(int(index) + 2, row.to_dict()) for index, row in frame.iterrows()]


def normalize_date(value: str) -> tuple[str | None, list[str]]:
    text = clean_cell(value)
    if not text:
        return None, ["date_missing"]
    lowered = text.lower()
    if "?" in text or any(marker in lowered for marker in VAGUE_DATE_MARKERS):
        return None, ["date_vague_preserved"]
    if re.fullmatch(r"\d{4}", text) or re.fullmatch(r"[A-Za-z]+ \d{4}", text):
        return None, ["date_vague_preserved"]
    cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "")
    for fmt in PRECISE_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat(), []
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        return parsed.date().isoformat(), []
    except ValueError:
        return None, ["date_unparsed_preserved"]


def parse_year(year_raw: str, source_date_raw: str, date_normalized: str | None) -> tuple[int | None, list[str]]:
    text = clean_cell(year_raw)
    if text:
        try:
            year = int(float(text))
            if 1500 <= year <= 2200:
                return year, []
        except ValueError:
            pass
        return None, ["year_unparsed_preserved"]
    if date_normalized:
        return int(date_normalized[:4]), []
    match = re.search(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2}|2200)\b", source_date_raw)
    return (int(match.group(1)), []) if match else (None, [])


def normalize_fatal(value: str) -> str:
    text = clean_cell(value)
    lowered = text.lower()
    if lowered in {"y", "yes", "fatal"}:
        return "Y"
    if lowered in {"n", "no", "non-fatal", "nonfatal"}:
        return "N"
    return text


def incident_type_candidate(original_type_raw: str) -> str:
    lowered = original_type_raw.lower()
    if has_any(lowered, QUESTIONABLE_MARKERS):
        return "questionable_or_unconfirmed_source"
    if "watercraft" in lowered or "boat" in lowered:
        return "watercraft_or_object_contact"
    if "sea disaster" in lowered:
        return "sea_disaster_context"
    if "provoked" in lowered or "unprovoked" in lowered:
        return "human_shark_interaction_candidate"
    return "unknown_incident_context"


def has_any(text: str, markers: set[str] | list[str] | tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def source_is_questionable(fields: dict[str, str]) -> bool:
    combined = " ".join(
        [
            fields.get("original_type_raw", ""),
            fields.get("investigator_or_source_raw", ""),
            fields.get("injury", ""),
        ]
    ).lower()
    return has_any(combined, QUESTIONABLE_MARKERS)


def classify_behavior(fields: dict[str, str]) -> tuple[str, str, list[str]]:
    warnings = ["behavior_hypothesis_provisional"]
    if source_is_questionable(fields):
        return "unknown_insufficient_evidence", "unknown", warnings + ["source_questionable_behavior_unknown"]

    activity = fields.get("activity", "").lower()
    injury = fields.get("injury", "").lower()
    original_type = fields.get("original_type_raw", "").lower()
    source = fields.get("investigator_or_source_raw", "").lower()
    combined = " ".join([activity, injury, original_type, source])

    no_bodily_injury = has_any(
        injury,
        (
            "no injury",
            "no injuries",
            "not injured",
            "uninjured",
            "no bodily injury",
            "no human injury",
        ),
    )
    if no_bodily_injury and has_any(
        combined,
        ("watercraft", "boat", "kayak", "canoe", "surfboard", "paddleboard", "board", "ski"),
    ):
        return "object_contact_or_investigative_bite", "weak", warnings

    if has_any(combined, ("spearfish", "spear fishing", "fishing", "chumming", "bait", "catch", "stringer")) and has_any(
        combined, ("fish", "bait", "catch", "speared", "stringer", "chum")
    ):
        return "competitive_food_response", "plausible", warnings

    if has_any(combined, ("carcass", "dead whale", "dead dolphin", "dead turtle", "dead seal", "scavenge")):
        return "scavenging_context", "weak", warnings

    if has_any(
        injury,
        (
            "consumed",
            "body not recovered",
            "missing body",
            "remains recovered",
            "repeated",
            "multiple bites",
            "fatal predation",
            "dismembered",
        ),
    ):
        confidence = "plausible" if fields.get("fatal_y_n") == "Y" else "weak"
        return "attempted_predation_event", confidence, warnings

    if has_any(combined, ("stepped on", "accidental", "bumped", "collision")):
        return "accidental_contact", "weak", warnings

    if has_any(combined, ("defensive", "displaced", "chased away", "territorial")):
        return "territorial_displacement", "weak", warnings

    return "unknown_insufficient_evidence", "unknown", warnings


def species_warnings(species_raw: str) -> list[str]:
    lowered = species_raw.lower()
    if lowered and has_any(lowered, ("questionable", "unconfirmed", "unverified", "not confirmed", "unknown")):
        return ["species_uncertain_preserved"]
    return []


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def row_fingerprint(record: dict[str, Any]) -> str:
    payload = {field: record.get(field) for field in FINGERPRINT_FIELDS}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def fallback_hash(record: dict[str, Any]) -> str:
    payload = {
        "source_date_raw": record.get("source_date_raw"),
        "date_normalized": record.get("date_normalized"),
        "country": record.get("country"),
        "area": record.get("area"),
        "location": record.get("location"),
        "activity": record.get("activity"),
        "injury": record.get("injury"),
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:24]


def match_key(record: dict[str, Any]) -> str:
    case_number = clean_cell(record.get("source_case_number", ""))
    if case_number:
        return f"case:{case_number.lower()}"
    return f"fallback:{fallback_hash(record)}"


def normalize_source_row(
    row: dict[str, Any],
    *,
    row_number: int,
    source_file: str,
    imported_at: str,
) -> dict[str, Any]:
    fields = {field: raw_value(row, field) for field in SOURCE_FIELDS}
    fields["fatal_y_n"] = normalize_fatal(fields["fatal_y_n"])
    date_normalized, warnings = normalize_date(fields["source_date_raw"])
    year, year_warnings = parse_year(fields["year"], fields["source_date_raw"], date_normalized)
    warnings.extend(year_warnings)
    warnings.extend(species_warnings(fields["species_raw"]))

    behavior_candidate, behavior_confidence, behavior_warnings = classify_behavior(fields)
    if behavior_candidate not in BEHAVIOR_CANDIDATES:
        behavior_candidate = "unknown_insufficient_evidence"
        behavior_confidence = "unknown"
        behavior_warnings.append("behavior_candidate_not_allowed")
    warnings.extend(behavior_warnings)

    record: dict[str, Any] = {
        "source_name": SOURCE_NAME,
        "source_file": source_file,
        "source_row_number": row_number,
        "source_case_number": fields["source_case_number"],
        "source_date_raw": fields["source_date_raw"],
        "date_normalized": date_normalized,
        "year": year,
        "country": fields["country"],
        "area": fields["area"],
        "location": fields["location"],
        "activity": fields["activity"],
        "sex": fields["sex"],
        "age": fields["age"],
        "injury": fields["injury"],
        "fatal_y_n": fields["fatal_y_n"],
        "time_raw": fields["time_raw"],
        "species_raw": fields["species_raw"],
        "investigator_or_source_raw": fields["investigator_or_source_raw"],
        "pdf_case_link_raw": fields["pdf_case_link_raw"],
        "original_type_raw": fields["original_type_raw"],
        "ai1sad_incident_type_candidate": incident_type_candidate(fields["original_type_raw"]),
        "ai1sad_behavioral_hypothesis_candidate": behavior_candidate,
        "ai1sad_behavioral_hypothesis_provisional": True,
        "ai1sad_behavior_confidence": behavior_confidence,
        "normalization_warnings": sorted(set(warnings)),
        "imported_at": imported_at,
    }
    record["row_fingerprint"] = row_fingerprint(record)
    record["match_key"] = match_key(record)
    return record


def source_row_has_content(row: dict[str, Any]) -> bool:
    return any(raw_value(row, field) for field in SOURCE_FIELDS)


def source_row_has_minimum_identity(row: dict[str, Any]) -> bool:
    return any(
        raw_value(row, field)
        for field in ("source_case_number", "source_date_raw", "country", "area", "location", "activity", "injury")
    )


def read_gsaf_file(path: str | Path, *, imported_at: str | None = None) -> tuple[list[dict[str, Any]], list[int]]:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    imported_at = imported_at or utc_now_iso()
    records: list[dict[str, Any]] = []
    malformed_rows: list[int] = []
    for row_number, row in read_tabular_rows(input_path):
        if not source_row_has_content(row):
            continue
        if not source_row_has_minimum_identity(row):
            malformed_rows.append(row_number)
            continue
        records.append(
            normalize_source_row(
                row,
                row_number=row_number,
                source_file=input_path.name,
                imported_at=imported_at,
            )
        )
    return records, malformed_rows


def duplicate_case_numbers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(record["source_case_number"] for record in records if record.get("source_case_number"))
    return [{"case_number": case_number, "count": count} for case_number, count in sorted(counts.items()) if count > 1]


def load_baseline(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    baseline_path = Path(path)
    if not baseline_path.exists():
        return {}
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("rows"), dict):
        return data["rows"]
    if isinstance(data, dict):
        return data
    return {}


def baseline_fingerprint(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        value = entry.get("row_fingerprint") or entry.get("fingerprint")
        return str(value) if value else None
    return None


def compare_against_baseline(records: list[dict[str, Any]], baseline_rows: dict[str, Any]) -> dict[str, Any]:
    current_keys: set[str] = set()
    new_keys: list[str] = []
    changed_keys: list[str] = []
    unchanged_keys: list[str] = []

    for record in records:
        key = record["match_key"]
        current_keys.add(key)
        previous = baseline_fingerprint(baseline_rows.get(key))
        if previous is None:
            new_keys.append(key)
        elif previous == record["row_fingerprint"]:
            unchanged_keys.append(key)
        else:
            changed_keys.append(key)

    removed_keys = sorted(set(baseline_rows) - current_keys)
    return {
        "new_rows": len(new_keys),
        "changed_rows": len(changed_keys),
        "unchanged_rows": len(unchanged_keys),
        "possibly_removed_rows": len(removed_keys),
        "new_match_keys": sorted(new_keys),
        "changed_match_keys": sorted(changed_keys),
        "unchanged_match_keys": sorted(unchanged_keys),
        "possibly_removed_match_keys": removed_keys,
    }


def warning_count(records: list[dict[str, Any]], prefix: str) -> int:
    return sum(
        1
        for record in records
        if any(str(warning).startswith(prefix) for warning in record.get("normalization_warnings", []))
    )


def build_baseline(records: list[dict[str, Any]], *, generated_at: str) -> dict[str, Any]:
    return {
        "source_name": SOURCE_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "row_key_strategy": "case number if present; otherwise date/country/area/location/activity/injury hash",
        "rows": {
            record["match_key"]: {
                "row_fingerprint": record["row_fingerprint"],
                "source_case_number": record.get("source_case_number"),
                "source_row_number": record.get("source_row_number"),
            }
            for record in records
        },
    }


def write_json(path: str | Path, payload: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_gsaf(
    input_path: str | Path,
    *,
    staging_path: str | Path = DEFAULT_STAGING_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    baseline_path: str | Path | None = DEFAULT_BASELINE_PATH,
    update_baseline: bool = False,
    imported_at: str | None = None,
) -> dict[str, Any]:
    imported_at = imported_at or utc_now_iso()
    input_file = Path(input_path)
    records, malformed_rows = read_gsaf_file(input_file, imported_at=imported_at)
    baseline_rows = load_baseline(baseline_path)
    delta = compare_against_baseline(records, baseline_rows)

    staging_payload = {
        "source_name": SOURCE_NAME,
        "schema_version": SCHEMA_VERSION,
        "source_file": input_file.name,
        "imported_at": imported_at,
        "records": records,
    }

    report: dict[str, Any] = {
        "source_name": SOURCE_NAME,
        "schema_version": SCHEMA_VERSION,
        "input_file": input_file.name,
        "imported_at": imported_at,
        "staging_file": str(staging_path),
        "report_file": str(report_path),
        "baseline_file": str(baseline_path) if baseline_path is not None else None,
        "baseline_found": bool(baseline_rows),
        "baseline_updated": False,
        "supported_file_formats": sorted(SUPPORTED_EXTENSIONS),
        "row_key_strategy": "case number if present; otherwise date/country/area/location/activity/injury hash",
        "total_rows": len(records),
        "malformed_rows": len(malformed_rows),
        "malformed_row_numbers": malformed_rows,
        "duplicate_case_numbers": duplicate_case_numbers(records),
        "date_parse_warnings": warning_count(records, "date_"),
        "species_parse_warnings": warning_count(records, "species_"),
        "behavior_mapping_warnings": warning_count(records, "behavior_")
        + warning_count(records, "source_questionable"),
        "side_effects": SIDE_EFFECTS,
        **delta,
    }

    write_json(staging_path, staging_payload)
    if update_baseline and baseline_path is not None:
        write_json(baseline_path, build_baseline(records, generated_at=imported_at))
        report["baseline_updated"] = True
    write_json(report_path, report)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a local GSAF spreadsheet into AI1SAD staging JSON.")
    parser.add_argument("--input", required=True, help="Path to a local GSAF .csv, .xls, or .xlsx file.")
    parser.add_argument("--staging", default=str(DEFAULT_STAGING_PATH), help="Normalized staging JSON output path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Import report JSON output path.")
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE_PATH), help="Baseline fingerprint JSON path.")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Replace the baseline fingerprint file after writing the report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    report = import_gsaf(
        args.input,
        staging_path=args.staging,
        report_path=args.report,
        baseline_path=args.baseline,
        update_baseline=args.update_baseline,
    )
    print(json.dumps({"status": "ok", "report_file": args.report, "total_rows": report["total_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
