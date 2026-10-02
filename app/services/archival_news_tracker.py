from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.services.incident_registry import SourceLink


ARCHIVAL_TRACKER_SCHEMA_VERSION = "phase_26c_v1"
SOURCE_NAME = "AI1SAD Australian Archival News Tracker"
MONGO_IMPORTER_NAME = "archival_news_tracker_manual_import"

SUPPORTED_IMPORT_EXTENSIONS = {".csv", ".json"}
DEFAULT_STAGING_PATH = Path("data/imports/archival_news/staging/latest_archival_sources.json")
DEFAULT_REPORT_PATH = Path("data/imports/archival_news/reports/latest_archival_import_report.json")

SOURCE_PLATFORMS = {
    "trove",
    "national_library_of_australia",
    "state_library_qld",
    "state_library_nsw",
    "state_library_victoria",
    "state_library_wa",
    "state_library_sa",
    "national_archives_of_australia",
    "local_newspaper_archive",
    "surf_lifesaving_archive",
    "government_archive",
    "maritime_archive",
    "other",
    "unknown",
}

SOURCE_KINDS = {
    "newspaper_article",
    "trove_metadata",
    "state_library_record",
    "government_report",
    "coroner_or_inquest",
    "surf_lifesaving_record",
    "maritime_record",
    "local_history",
    "catalogue_record",
    "unknown",
}

CAPTURE_METHODS = {
    "manual_metadata_entry",
    "manual_citation_entry",
    "manual_catalogue_entry",
    "analyst_note",
}

BLOCKED_CAPTURE_METHODS = {
    "scrape",
    "scraping",
    "web_scrape",
    "trove_api",
    "archive_api",
    "bulk_download",
    "article_body_download",
    "ocr_dump",
}

EXTRACTION_STATUSES = {
    "metadata_only",
    "citation_only",
    "ocr_needs_review",
    "excerpt_reviewed",
    "rights_review_required",
    "rejected",
}

REVIEW_STATUSES = {
    "unreviewed",
    "metadata_captured",
    "ocr_needs_review",
    "citation_verified",
    "case_link_candidate",
    "case_link_confirmed",
    "duplicate_or_reprint",
    "rights_review_required",
    "rejected",
}

SOURCE_CONFIDENCE_VALUES = {
    "unreviewed",
    "weak",
    "plausible",
    "corroborated",
    "conflicting",
    "contradicted",
}

COPYRIGHT_STATUSES = {
    "unknown",
    "citation_only",
    "public_domain",
    "open_license",
    "copyrighted",
    "rights_restricted",
    "rights_review_required",
}

OCR_CONFIDENCE_VALUES = {"unknown", "low", "medium", "high", "not_applicable"}

DUPLICATE_RELATIONS = {
    "none",
    "duplicate",
    "reprint",
    "syndicated",
    "later_retelling",
    "same_incident_possible",
    "unknown",
}

CONFLICT_TYPES = {
    "date_disagreement",
    "location_disagreement",
    "identity_disagreement",
    "species_disagreement",
    "fatality_disagreement",
    "injury_disagreement",
    "behavioral_interpretation_disagreement",
    "source_reliability_disagreement",
    "rights_disagreement",
}

PROHIBITED_TEXT_KEYS = {
    "article_body",
    "downloaded_html",
    "full_article_text",
    "full_copyrighted_article_text",
    "raw_article_text",
    "raw_ocr_text",
    "ocr_text_full",
}

SIDE_EFFECTS = {
    "scrapes_sources": False,
    "uses_trove_api": False,
    "downloads_article_bodies": False,
    "stores_full_article_text": False,
    "creates_warnings": False,
    "creates_alerts": False,
    "creates_public_feed_entries": False,
    "creates_replay_facts": False,
    "creates_drone_observations": False,
    "alters_scoring": False,
    "alters_replay": False,
}

PRIVATE_OUTPUT_FIELDS = {
    "notes_private",
    "people_mentioned",
}

CSV_LIST_FIELDS = {
    "people_mentioned",
    "related_source_ids",
    "claim_tags",
    "provenance_notes",
    "normalization_warnings",
}
CSV_JSON_FIELDS = {"conflicts"}


class ArchivalConflict(BaseModel):
    conflict_id: str
    conflict_type: str = "source_reliability_disagreement"
    summary: str
    conflicting_source_ids: list[str] = Field(default_factory=list)
    current_resolution: str = "unresolved"
    resolution_confidence: str = "unreviewed"
    public_summary_allowed: bool = False
    notes_private: str | None = None


class ArchivalSourceRecord(BaseModel):
    archival_source_id: str
    tracker_schema_version: str = ARCHIVAL_TRACKER_SCHEMA_VERSION
    created_at: datetime
    updated_at: datetime
    capture_method: str = "manual_metadata_entry"
    source_platform: str = "unknown"
    source_kind: str = "newspaper_article"
    archive_collection: str | None = None
    newspaper_title: str | None = None
    publication_date: str | None = None
    article_title: str | None = None
    article_url: str | None = None
    trove_article_id: str | None = None
    page_url: str | None = None
    page_number: str | None = None
    jurisdiction: str | None = None
    location_mentioned: str | None = None
    shark_attack_case_candidate: bool = False
    people_mentioned: list[str] = Field(default_factory=list)
    species_mentioned_raw: str | None = None
    incident_date_raw: str | None = None
    incident_date_normalized: str | None = None
    source_text_excerpt_allowed: bool = False
    source_text_excerpt: str | None = None
    copyright_status: str = "unknown"
    rights_note: str | None = None
    access_note: str | None = None
    citation: str | None = None
    extraction_status: str = "metadata_only"
    review_status: str = "unreviewed"
    linked_ai1sad_case_id: str | None = None
    source_confidence: str = "unreviewed"
    ocr_confidence: str = "unknown"
    ocr_uncertainty_notes: str | None = None
    public_citation_allowed: bool = False
    duplicate_group_id: str | None = None
    duplicate_relation: str = "none"
    duplicate_of_source_id: str | None = None
    related_source_ids: list[str] = Field(default_factory=list)
    claim_tags: list[str] = Field(default_factory=list)
    conflicts: list[ArchivalConflict] = Field(default_factory=list)
    provenance_notes: list[str] = Field(default_factory=list)
    normalization_warnings: list[str] = Field(default_factory=list)
    notes_private: str | None = None
    source_fingerprint: str
    metadata_only: bool = True
    article_body_stored: bool = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def archival_tracker_side_effects() -> dict[str, bool]:
    return dict(SIDE_EFFECTS)


def create_archival_record(payload: dict[str, Any], *, now: datetime | None = None) -> ArchivalSourceRecord:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    _reject_article_body_keys(payload)
    timestamp = now or utc_now()
    data = dict(payload)
    warnings = list_field(data.get("normalization_warnings"), "normalization_warnings")
    archival_source_id = safe_identifier(data.get("archival_source_id"), "archival_source_id", prefix="archive")

    capture_method = choice_or_default(
        data.get("capture_method"),
        CAPTURE_METHODS,
        "capture_method",
        "manual_metadata_entry",
        blocked=BLOCKED_CAPTURE_METHODS,
    )
    source_platform = choice_or_default(data.get("source_platform"), SOURCE_PLATFORMS, "source_platform", "unknown")
    source_kind = choice_or_default(data.get("source_kind"), SOURCE_KINDS, "source_kind", "newspaper_article")
    extraction_status = choice_or_default(
        data.get("extraction_status"),
        EXTRACTION_STATUSES,
        "extraction_status",
        "metadata_only",
    )
    review_status = choice_or_default(data.get("review_status"), REVIEW_STATUSES, "review_status", "unreviewed")
    source_confidence = choice_or_default(
        data.get("source_confidence"),
        SOURCE_CONFIDENCE_VALUES,
        "source_confidence",
        "unreviewed",
    )
    copyright_status = choice_or_default(
        data.get("copyright_status"),
        COPYRIGHT_STATUSES,
        "copyright_status",
        "unknown",
    )
    ocr_confidence = choice_or_default(data.get("ocr_confidence"), OCR_CONFIDENCE_VALUES, "ocr_confidence", "unknown")
    duplicate_relation = choice_or_default(
        data.get("duplicate_relation"),
        DUPLICATE_RELATIONS,
        "duplicate_relation",
        "none",
    )

    source_text_excerpt_allowed = bool_field(data.get("source_text_excerpt_allowed"), False)
    source_text_excerpt = bounded_text(data.get("source_text_excerpt"), "source_text_excerpt", 500) or None
    if source_text_excerpt and not source_text_excerpt_allowed:
        source_text_excerpt = None
        warnings.append("excerpt_suppressed_rights_not_allowed")
    if source_text_excerpt_allowed and copyright_status in {"unknown", "rights_review_required", "rights_restricted"}:
        warnings.append("excerpt_requires_rights_review")

    article_url = safe_url(data.get("article_url"), "article_url")
    page_url = safe_url(data.get("page_url"), "page_url")
    citation = bounded_text(data.get("citation"), "citation", 500) or None
    citation = citation or build_citation(data)
    if not citation:
        warnings.append("citation_missing")

    conflicts = [_coerce_conflict(item) for item in data.get("conflicts", [])]
    record_data: dict[str, Any] = {
        "archival_source_id": archival_source_id,
        "tracker_schema_version": ARCHIVAL_TRACKER_SCHEMA_VERSION,
        "created_at": data.get("created_at", timestamp),
        "updated_at": data.get("updated_at", timestamp),
        "capture_method": capture_method,
        "source_platform": source_platform,
        "source_kind": source_kind,
        "archive_collection": bounded_text(data.get("archive_collection"), "archive_collection", 180) or None,
        "newspaper_title": bounded_text(data.get("newspaper_title"), "newspaper_title", 180) or None,
        "publication_date": bounded_text(data.get("publication_date"), "publication_date", 80) or None,
        "article_title": bounded_text(data.get("article_title"), "article_title", 240) or None,
        "article_url": article_url,
        "trove_article_id": bounded_text(data.get("trove_article_id"), "trove_article_id", 90) or None,
        "page_url": page_url,
        "page_number": bounded_text(data.get("page_number"), "page_number", 40) or None,
        "jurisdiction": bounded_text(data.get("jurisdiction"), "jurisdiction", 120) or None,
        "location_mentioned": bounded_text(data.get("location_mentioned"), "location_mentioned", 180) or None,
        "shark_attack_case_candidate": bool_field(data.get("shark_attack_case_candidate"), False),
        "people_mentioned": list_field(data.get("people_mentioned"), "people_mentioned", max_items=20, max_item_length=120),
        "species_mentioned_raw": bounded_text(data.get("species_mentioned_raw"), "species_mentioned_raw", 180) or None,
        "incident_date_raw": bounded_text(data.get("incident_date_raw"), "incident_date_raw", 120) or None,
        "incident_date_normalized": bounded_text(data.get("incident_date_normalized"), "incident_date_normalized", 40) or None,
        "source_text_excerpt_allowed": source_text_excerpt_allowed,
        "source_text_excerpt": source_text_excerpt,
        "copyright_status": copyright_status,
        "rights_note": bounded_text(data.get("rights_note"), "rights_note", 500) or None,
        "access_note": bounded_text(data.get("access_note"), "access_note", 500) or None,
        "citation": citation,
        "extraction_status": extraction_status,
        "review_status": review_status,
        "linked_ai1sad_case_id": safe_optional_identifier(data.get("linked_ai1sad_case_id"), "linked_ai1sad_case_id"),
        "source_confidence": source_confidence,
        "ocr_confidence": ocr_confidence,
        "ocr_uncertainty_notes": bounded_text(data.get("ocr_uncertainty_notes"), "ocr_uncertainty_notes", 500) or None,
        "public_citation_allowed": bool_field(data.get("public_citation_allowed"), False),
        "duplicate_group_id": safe_optional_identifier(data.get("duplicate_group_id"), "duplicate_group_id"),
        "duplicate_relation": duplicate_relation,
        "duplicate_of_source_id": safe_optional_identifier(data.get("duplicate_of_source_id"), "duplicate_of_source_id"),
        "related_source_ids": list_field(data.get("related_source_ids"), "related_source_ids", max_items=30),
        "claim_tags": list_field(data.get("claim_tags"), "claim_tags", max_items=30),
        "conflicts": conflicts,
        "provenance_notes": list_field(data.get("provenance_notes"), "provenance_notes", max_items=30, max_item_length=240),
        "normalization_warnings": sorted(set(warnings)),
        "notes_private": bounded_text(data.get("notes_private"), "notes_private", 1200) or None,
        "metadata_only": True,
        "article_body_stored": False,
    }
    record_data["source_fingerprint"] = source_fingerprint(record_data)
    return ArchivalSourceRecord(**record_data)


def source_link_from_archival_record(record: ArchivalSourceRecord) -> SourceLink:
    return SourceLink(
        source_id=f"archival:{record.archival_source_id}",
        source_type=registry_source_type(record),
        source_name=record.newspaper_title or record.archive_collection or record.source_platform,
        source_ref=record.trove_article_id or record.citation or record.archival_source_id,
        source_url=record.article_url or record.page_url,
        source_date=record.publication_date,
        source_title=record.article_title,
        source_rights_note=record.rights_note or "Citation metadata only; article body not redistributed.",
        source_confidence=record.source_confidence,
        linked_claims=source_link_claims(record),
        quote_excerpt_allowed=record.source_text_excerpt_allowed and bool(record.source_text_excerpt),
        quote_excerpt=record.source_text_excerpt if record.source_text_excerpt_allowed else None,
        public_citation_allowed=record.public_citation_allowed,
        private_notes=(
            f"archival_source_id={record.archival_source_id}; "
            f"review_status={record.review_status}; extraction_status={record.extraction_status}"
        ),
    )


def public_archival_source_output(record: ArchivalSourceRecord) -> dict[str, Any]:
    output = {
        "archival_source_id": record.archival_source_id,
        "tracker_schema_version": record.tracker_schema_version,
        "source_platform": record.source_platform,
        "source_kind": record.source_kind,
        "archive_collection": record.archive_collection,
        "newspaper_title": record.newspaper_title,
        "publication_date": record.publication_date,
        "article_title": record.article_title,
        "article_url": record.article_url if record.public_citation_allowed else None,
        "trove_article_id": record.trove_article_id,
        "page_url": record.page_url if record.public_citation_allowed else None,
        "page_number": record.page_number,
        "jurisdiction": record.jurisdiction,
        "location_mentioned": record.location_mentioned,
        "shark_attack_case_candidate": record.shark_attack_case_candidate,
        "species_mentioned_raw": record.species_mentioned_raw,
        "incident_date_raw": record.incident_date_raw,
        "incident_date_normalized": record.incident_date_normalized,
        "source_text_excerpt": record.source_text_excerpt if record.source_text_excerpt_allowed else None,
        "copyright_status": record.copyright_status,
        "rights_note": record.rights_note,
        "access_note": record.access_note,
        "citation": record.citation,
        "extraction_status": record.extraction_status,
        "review_status": record.review_status,
        "linked_ai1sad_case_id": record.linked_ai1sad_case_id,
        "source_confidence": record.source_confidence,
        "ocr_confidence": record.ocr_confidence,
        "ocr_uncertainty_notes": record.ocr_uncertainty_notes,
        "public_citation_allowed": record.public_citation_allowed,
        "duplicate_group_id": record.duplicate_group_id,
        "duplicate_relation": record.duplicate_relation,
        "duplicate_of_source_id": record.duplicate_of_source_id,
        "related_source_ids": record.related_source_ids,
        "claim_tags": record.claim_tags,
        "conflicts": [
            {
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type,
                "summary": conflict.summary,
                "conflicting_source_ids": conflict.conflicting_source_ids,
                "current_resolution": conflict.current_resolution,
                "resolution_confidence": conflict.resolution_confidence,
            }
            for conflict in record.conflicts
            if conflict.public_summary_allowed
        ],
        "provenance_notes": record.provenance_notes,
        "normalization_warnings": record.normalization_warnings,
        "metadata_only": True,
        "article_body_stored": False,
        "side_effects": archival_tracker_side_effects(),
    }
    return {key: value for key, value in output.items() if key not in PRIVATE_OUTPUT_FIELDS and value not in (None, [], "")}


def import_archival_sources(
    input_path: str | Path,
    *,
    staging_path: str | Path = DEFAULT_STAGING_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    imported_at: datetime | None = None,
    mongo_database: Any | None = None,
) -> dict[str, Any]:
    input_file = Path(input_path)
    imported_at = imported_at or utc_now()
    payloads = read_archival_input(input_file)
    records: list[ArchivalSourceRecord] = []
    errors: list[dict[str, Any]] = []

    for index, payload in enumerate(payloads, start=1):
        try:
            records.append(create_archival_record(payload, now=imported_at))
        except (TypeError, ValueError) as exc:
            errors.append(
                {
                    "row_number": index,
                    "archival_source_id": str(payload.get("archival_source_id") or ""),
                    "error": str(exc),
                }
            )

    staging_payload = {
        "source_name": SOURCE_NAME,
        "tracker_schema_version": ARCHIVAL_TRACKER_SCHEMA_VERSION,
        "input_file": input_file.name,
        "imported_at": imported_at.isoformat(),
        "metadata_only": True,
        "article_body_stored": False,
        "side_effects": archival_tracker_side_effects(),
        "records": [record.model_dump(mode="json") for record in records],
        "registry_source_links": [
            source_link_from_archival_record(record).model_dump(mode="json")
            for record in records
        ],
        "public_records": [public_archival_source_output(record) for record in records],
    }
    report = {
        "source_name": SOURCE_NAME,
        "tracker_schema_version": ARCHIVAL_TRACKER_SCHEMA_VERSION,
        "input_file": input_file.name,
        "imported_at": imported_at.isoformat(),
        "staging_file": str(staging_path),
        "report_file": str(report_path),
        "supported_file_formats": sorted(SUPPORTED_IMPORT_EXTENSIONS),
        "total_rows": len(payloads),
        "records_written": len(records),
        "rejected_rows": len(errors),
        "errors": errors,
        "metadata_only": True,
        "article_body_stored": False,
        "side_effects": archival_tracker_side_effects(),
    }
    if mongo_database is not None:
        report["mongo_persistence"] = persist_archival_import_to_mongo(
            mongo_database,
            records,
            report,
            input_file=input_file,
            imported_at=imported_at,
        )
    write_json(staging_path, staging_payload)
    write_json(report_path, report)
    return report


def persist_archival_import_to_mongo(
    db: Any,
    records: list[ArchivalSourceRecord],
    report: dict[str, Any],
    *,
    input_file: Path,
    imported_at: datetime,
) -> dict[str, Any]:
    from app.mongodb import COLLECTIONS

    sources = db[COLLECTIONS["archival_sources"]]
    reports = db[COLLECTIONS["archival_import_reports"]]
    records_upserted = 0
    for record in records:
        document = archival_mongo_document(record, input_file=input_file, imported_at=imported_at)
        sources.replace_one({"archival_source_id": record.archival_source_id}, document, upsert=True)
        records_upserted += 1

    report_document = archival_import_report_mongo_document(report, input_file=input_file, imported_at=imported_at)
    reports.insert_one(report_document)
    return {
        "enabled": True,
        "collection": COLLECTIONS["archival_sources"],
        "report_collection": COLLECTIONS["archival_import_reports"],
        "records_upserted": records_upserted,
        "reports_inserted": 1,
        "visibility": "internal",
        "metadata_only": True,
        "article_body_stored": False,
    }


def archival_mongo_document(
    record: ArchivalSourceRecord,
    *,
    input_file: Path,
    imported_at: datetime,
) -> dict[str, Any]:
    document = record.model_dump(mode="json")
    document.update(
        {
            "visibility": "internal",
            "public_visibility": "restricted",
            "ingest_source": MONGO_IMPORTER_NAME,
            "input_file": input_file.name,
            "last_imported_at": imported_at.isoformat(),
            "metadata_only": True,
            "article_body_stored": False,
            "side_effects": archival_tracker_side_effects(),
        }
    )
    return document


def archival_import_report_mongo_document(
    report: dict[str, Any],
    *,
    input_file: Path,
    imported_at: datetime,
) -> dict[str, Any]:
    return {
        **report,
        "visibility": "internal",
        "ingest_source": MONGO_IMPORTER_NAME,
        "input_file": input_file.name,
        "imported_at": imported_at.isoformat(),
        "metadata_only": True,
        "article_body_stored": False,
        "side_effects": archival_tracker_side_effects(),
    }


def read_archival_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_IMPORT_EXTENSIONS:
        raise ValueError(f"Unsupported archival source input format: {suffix}")
    if suffix == ".json":
        return read_json_archival_rows(path)
    return read_csv_archival_rows(path)


def read_json_archival_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("records"), list):
        rows = data["records"]
    elif isinstance(data, dict) and isinstance(data.get("sources"), list):
        rows = data["sources"]
    elif isinstance(data, dict) and data.get("archival_source_id"):
        rows = [data]
    else:
        raise ValueError("JSON archival input must be a record, list, or object with records/sources")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("JSON archival rows must be objects")
    return [dict(row) for row in rows]


def read_csv_archival_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [csv_row_payload(row) for row in reader]


def csv_row_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            continue
        field = key.strip()
        text = "" if value is None else str(value).strip()
        if not field or not text:
            continue
        if field in CSV_LIST_FIELDS:
            payload[field] = csv_list_value(text)
        elif field in CSV_JSON_FIELDS:
            payload[field] = json.loads(text)
        else:
            payload[field] = text
    return payload


def csv_list_value(value: str) -> list[str]:
    if value.startswith("["):
        data = json.loads(value)
        if not isinstance(data, list):
            raise ValueError("CSV list field JSON value must be a list")
        return [str(item).strip() for item in data if str(item).strip()]
    return [item.strip() for item in value.split(";") if item.strip()]


def write_json(path: str | Path, payload: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import local/manual archival source metadata into AI1SAD staging JSON.")
    parser.add_argument("--input", required=True, help="Path to a local archival source metadata .json or .csv file.")
    parser.add_argument(
        "--staging",
        default=str(DEFAULT_STAGING_PATH),
        help="Normalized metadata-only staging JSON output path.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Metadata import report JSON output path.",
    )
    parser.add_argument(
        "--mongo",
        action="store_true",
        help="Also persist accepted metadata records and the import report to configured MongoDB.",
    )
    parser.add_argument(
        "--skip-mongo-indexes",
        action="store_true",
        help="Skip archival MongoDB index creation when --mongo is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    mongo_database = None
    if args.mongo:
        from app.mongodb import ensure_archival_tracker_indexes, get_database

        mongo_database = get_database()
        if not args.skip_mongo_indexes:
            ensure_archival_tracker_indexes(mongo_database)
    report = import_archival_sources(
        args.input,
        staging_path=args.staging,
        report_path=args.report,
        mongo_database=mongo_database,
    )
    print(
        json.dumps(
            {
                "status": "ok" if report["rejected_rows"] == 0 else "errors",
                "report_file": args.report,
                "records_written": report["records_written"],
                "rejected_rows": report["rejected_rows"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["rejected_rows"] == 0 else 1


def registry_source_type(record: ArchivalSourceRecord) -> str:
    if record.source_kind == "trove_metadata":
        return "trove_metadata"
    if record.source_kind == "state_library_record":
        return "state_library_record"
    if record.source_kind == "government_report":
        return "government_report"
    if record.source_kind == "coroner_or_inquest":
        return "coroner_or_inquest"
    if record.source_kind == "surf_lifesaving_record":
        return "surf_lifesaving_record"
    return "archival_newspaper"


def source_link_claims(record: ArchivalSourceRecord) -> list[str]:
    claims = []
    if record.incident_date_raw or record.incident_date_normalized:
        claims.append("incident_date")
    if record.location_mentioned:
        claims.append("location")
    if record.species_mentioned_raw:
        claims.append("species_raw")
    if record.shark_attack_case_candidate:
        claims.append("case_candidate")
    if record.ocr_confidence != "not_applicable":
        claims.append("ocr_review_state")
    if record.duplicate_relation != "none":
        claims.append("duplicate_or_reprint_context")
    return claims


def build_citation(data: dict[str, Any]) -> str | None:
    parts = [
        bounded_text(data.get("newspaper_title"), "newspaper_title", 180),
        bounded_text(data.get("article_title"), "article_title", 240),
        bounded_text(data.get("publication_date"), "publication_date", 80),
        bounded_text(data.get("page_number"), "page_number", 40),
    ]
    citation = ", ".join(part for part in parts if part)
    return citation or None


def source_fingerprint(data: dict[str, Any]) -> str:
    basis = "|".join(
        str(data.get(key) or "")
        for key in (
            "source_platform",
            "archive_collection",
            "newspaper_title",
            "publication_date",
            "article_title",
            "article_url",
            "trove_article_id",
            "page_url",
            "page_number",
            "citation",
        )
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _coerce_conflict(item: ArchivalConflict | dict[str, Any]) -> ArchivalConflict:
    conflict = item if isinstance(item, ArchivalConflict) else ArchivalConflict(**item)
    updates: dict[str, Any] = {}
    if conflict.conflict_type not in CONFLICT_TYPES:
        updates["conflict_type"] = "source_reliability_disagreement"
    if conflict.resolution_confidence not in SOURCE_CONFIDENCE_VALUES:
        updates["resolution_confidence"] = "unreviewed"
    return conflict.model_copy(update=updates) if updates else conflict


def _reject_article_body_keys(payload: dict[str, Any]) -> None:
    prohibited = PROHIBITED_TEXT_KEYS.intersection(payload)
    if prohibited:
        names = ", ".join(sorted(prohibited))
        raise ValueError(f"full article text is not accepted by the archival tracker: {names}")


def choice_or_default(
    value: Any,
    allowed: set[str],
    field: str,
    default: str,
    *,
    blocked: set[str] | None = None,
) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    if blocked and text in blocked:
        raise ValueError(f"{field} must not use scraping, API, or bulk-download capture modes")
    if text not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return text


def bool_field(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    raise ValueError("boolean field must be true or false")


def bounded_text(value: Any, field: str, max_length: int) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return text


def list_field(value: Any, field: str, *, max_items: int = 20, max_item_length: int = 120) -> list[str]:
    if value is None or value == "":
        return []
    items = value if isinstance(value, list) else [value]
    if len(items) > max_items:
        raise ValueError(f"{field} must contain at most {max_items} items")
    output: list[str] = []
    for item in items:
        text = bounded_text(item, field, max_item_length)
        if text:
            output.append(text)
    return output


def safe_identifier(value: Any, field: str, *, prefix: str) -> str:
    text = bounded_text(value, field, 100)
    if not text:
        text = f"{prefix}-{uuid4().hex[:12]}"
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", text):
        raise ValueError(f"{field} must contain only letters, numbers, dots, colons, underscores, or hyphens")
    return text


def safe_optional_identifier(value: Any, field: str) -> str | None:
    text = bounded_text(value, field, 100)
    if not text:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", text):
        raise ValueError(f"{field} must contain only letters, numbers, dots, colons, underscores, or hyphens")
    return text


def safe_url(value: Any, field: str) -> str | None:
    text = bounded_text(value, field, 500)
    if not text:
        return None
    if not re.match(r"^https://", text):
        raise ValueError(f"{field} must be an https URL")
    return text


if __name__ == "__main__":
    raise SystemExit(main())
