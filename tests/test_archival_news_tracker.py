from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.mongodb import COLLECTIONS
from app.services.archival_news_tracker import (
    ARCHIVAL_TRACKER_SCHEMA_VERSION,
    archival_tracker_side_effects,
    create_archival_record,
    import_archival_sources,
    main,
    public_archival_source_output,
    source_link_from_archival_record,
)
from app.services.incident_registry import create_registry_record, public_safe_registry_output


NOW = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)


class FakeMongoCollection:
    def __init__(self):
        self.replacements = []
        self.inserted = []
        self.indexes = []

    def replace_one(self, filter_query, document, upsert=False):
        self.replacements.append(
            {
                "filter": filter_query,
                "document": document,
                "upsert": upsert,
            }
        )

    def insert_one(self, document):
        self.inserted.append(document)

    def create_index(self, keys, **kwargs):
        self.indexes.append({"keys": keys, "kwargs": kwargs})


class FakeMongoDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = FakeMongoCollection()
        return self.collections[name]


def synthetic_archival_payload() -> dict:
    return {
        "archival_source_id": "trove:article:SYN-1901",
        "capture_method": "manual_metadata_entry",
        "source_platform": "trove",
        "source_kind": "newspaper_article",
        "archive_collection": "Trove / National Library of Australia",
        "newspaper_title": "Synthetic Coastal Gazette",
        "publication_date": "1901-06-02",
        "article_title": "Reported shark incident near Example Beach",
        "article_url": "https://trove.example.invalid/newspaper/article/SYN-1901",
        "trove_article_id": "SYN-1901",
        "page_url": "https://trove.example.invalid/newspaper/page/SYN-PAGE",
        "page_number": "2",
        "jurisdiction": "Queensland",
        "location_mentioned": "Example Beach",
        "shark_attack_case_candidate": True,
        "people_mentioned": ["Private Person"],
        "species_mentioned_raw": "large shark, unconfirmed",
        "incident_date_raw": "late May 1901",
        "incident_date_normalized": None,
        "source_text_excerpt_allowed": True,
        "source_text_excerpt": "Short rights-reviewed synthetic excerpt.",
        "copyright_status": "public_domain",
        "rights_note": "Synthetic public-domain metadata only; no article body.",
        "access_note": "Manual citation captured from catalogue metadata.",
        "citation": "Synthetic Coastal Gazette, 2 June 1901, p. 2.",
        "extraction_status": "excerpt_reviewed",
        "review_status": "case_link_candidate",
        "linked_ai1sad_case_id": "AI1SAD-SYN-0001",
        "source_confidence": "plausible",
        "ocr_confidence": "low",
        "ocr_uncertainty_notes": "Synthetic OCR uncertainty retained for review.",
        "public_citation_allowed": True,
        "duplicate_group_id": "dup:example-beach-1901",
        "duplicate_relation": "same_incident_possible",
        "related_source_ids": ["trove:article:SYN-1901-REPRINT"],
        "claim_tags": ["incident_date", "location", "species_raw"],
        "conflicts": [
            {
                "conflict_id": "conflict:archive:SYN-1901:date",
                "conflict_type": "date_disagreement",
                "summary": "Synthetic article date conflicts with a later retelling.",
                "conflicting_source_ids": ["trove:article:SYN-1901", "trove:article:SYN-1901-REPRINT"],
                "current_resolution": "retain_source_dates_pending_review",
                "resolution_confidence": "weak",
                "public_summary_allowed": True,
                "notes_private": "Private conflict note.",
            }
        ],
        "provenance_notes": ["Synthetic metadata-only archival fixture."],
        "notes_private": "Private analyst note.",
    }


def test_create_archival_record_preserves_metadata_and_no_side_effects():
    record = create_archival_record(synthetic_archival_payload(), now=NOW)

    assert record.tracker_schema_version == ARCHIVAL_TRACKER_SCHEMA_VERSION
    assert record.created_at == NOW
    assert record.updated_at == NOW
    assert record.archival_source_id == "trove:article:SYN-1901"
    assert record.source_platform == "trove"
    assert record.source_kind == "newspaper_article"
    assert record.metadata_only is True
    assert record.article_body_stored is False
    assert record.source_fingerprint
    assert record.source_text_excerpt == "Short rights-reviewed synthetic excerpt."
    assert record.conflicts[0].conflict_type == "date_disagreement"
    assert archival_tracker_side_effects() == {
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


def test_archival_record_rejects_article_bodies_scraping_and_api_capture_modes():
    with pytest.raises(ValueError, match="full article text"):
        create_archival_record({**synthetic_archival_payload(), "full_article_text": "Do not store this."}, now=NOW)

    with pytest.raises(ValueError, match="scraping, API, or bulk-download"):
        create_archival_record({**synthetic_archival_payload(), "capture_method": "trove_api"}, now=NOW)

    with pytest.raises(ValueError, match="scraping, API, or bulk-download"):
        create_archival_record({**synthetic_archival_payload(), "capture_method": "web_scrape"}, now=NOW)


def test_archival_public_output_filters_private_people_and_unapproved_excerpts():
    payload = {
        **synthetic_archival_payload(),
        "source_text_excerpt_allowed": False,
        "source_text_excerpt": "This should not be retained.",
        "public_citation_allowed": False,
    }
    record = create_archival_record(payload, now=NOW)
    public = public_archival_source_output(record)
    rendered = str(public)

    assert record.source_text_excerpt is None
    assert "excerpt_suppressed_rights_not_allowed" in record.normalization_warnings
    assert "Private Person" not in rendered
    assert "Private analyst note" not in rendered
    assert "Private conflict note" not in rendered
    assert "This should not be retained." not in rendered
    assert "article_body_stored" in public
    assert public["article_body_stored"] is False
    assert public["side_effects"]["uses_trove_api"] is False


def test_archival_source_link_can_attach_to_registry_without_promoting_claims():
    record = create_archival_record(synthetic_archival_payload(), now=NOW)
    source_link = source_link_from_archival_record(record)
    registry = create_registry_record(
        {
            "ai1sad_case_id": "AI1SAD-SYN-0001",
            "review_status": "source_review",
            "public_visibility": "restricted",
            "incident_date_raw": "late May 1901",
            "country": "Australia",
            "region": "Queensland",
            "location": "Example Beach",
            "official_species_status": "unconfirmed",
            "official_species_name": None,
            "official_species_source_id": None,
            "source_links": [source_link],
            "species_claims": [
                {
                    "species_raw": record.species_mentioned_raw,
                    "normalized_species": None,
                    "source_ids": [source_link.source_id],
                    "confidence": "weak",
                }
            ],
            "internal_species_hypotheses": [],
            "species_disclosure_risk": "moderate",
            "behavioral_hypotheses": [
                {
                    "hypothesis": "unknown_insufficient_evidence",
                    "confidence": "unknown",
                    "source_ids": [source_link.source_id],
                }
            ],
            "normalization_warnings": ["archival_source_claim_unreviewed"],
        },
        now=NOW,
    )
    public_registry = public_safe_registry_output(registry)

    assert source_link.source_type == "archival_newspaper"
    assert source_link.source_id == "archival:trove:article:SYN-1901"
    assert source_link.source_name == "Synthetic Coastal Gazette"
    assert source_link.quote_excerpt_allowed is True
    assert "species_raw" in source_link.linked_claims
    assert registry.official_species_status == "unconfirmed"
    assert registry.official_species_name is None
    assert registry.internal_species_hypotheses == []
    assert registry.primary_behavioral_hypothesis == "unknown_insufficient_evidence"
    assert public_registry["official_species_name"] is None
    assert "large shark" not in str(public_registry["internal_species_hypotheses"]).lower()


def test_archival_record_tracks_duplicate_reprint_and_public_conflict_summary():
    record = create_archival_record(
        {
            **synthetic_archival_payload(),
            "archival_source_id": "trove:article:SYN-1901-REPRINT",
            "duplicate_relation": "reprint",
            "duplicate_of_source_id": "trove:article:SYN-1901",
            "review_status": "duplicate_or_reprint",
        },
        now=NOW,
    )
    public = public_archival_source_output(record)

    assert record.duplicate_relation == "reprint"
    assert record.duplicate_of_source_id == "trove:article:SYN-1901"
    assert public["duplicate_relation"] == "reprint"
    assert public["conflicts"][0]["summary"] == "Synthetic article date conflicts with a later retelling."


def test_archival_json_import_writes_metadata_staging_report_and_source_links(tmp_path):
    input_path = tmp_path / "archival_sources.json"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    input_path.write_text(
        '[{"archival_source_id":"trove:article:SYN-1901","source_platform":"trove",'
        '"source_kind":"newspaper_article","newspaper_title":"Synthetic Coastal Gazette",'
        '"publication_date":"1901-06-02","article_title":"Reported shark incident near Example Beach",'
        '"citation":"Synthetic Coastal Gazette, 2 June 1901, p. 2.",'
        '"copyright_status":"citation_only","source_confidence":"weak"}]\n',
        encoding="utf-8",
    )

    report = import_archival_sources(
        input_path,
        staging_path=staging_path,
        report_path=report_path,
        imported_at=NOW,
    )

    staging_text = staging_path.read_text(encoding="utf-8")
    report_text = report_path.read_text(encoding="utf-8")
    assert report["total_rows"] == 1
    assert report["records_written"] == 1
    assert report["rejected_rows"] == 0
    assert '"metadata_only": true' in staging_text
    assert '"article_body_stored": false' in staging_text
    assert '"registry_source_links"' in staging_text
    assert '"uses_trove_api": false' in report_text
    assert '"downloads_article_bodies": false' in report_text


def test_archival_csv_import_splits_manual_list_fields(tmp_path):
    input_path = tmp_path / "archival_sources.csv"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    input_path.write_text(
        "archival_source_id,source_platform,source_kind,newspaper_title,publication_date,citation,claim_tags,related_source_ids\n"
        "trove:article:SYN-1901,trove,newspaper_article,Synthetic Coastal Gazette,1901-06-02,"
        '"Synthetic Coastal Gazette, 2 June 1901, p. 2.",incident_date;location,trove:article:SYN-1901-REPRINT\n',
        encoding="utf-8",
    )

    report = import_archival_sources(
        input_path,
        staging_path=staging_path,
        report_path=report_path,
        imported_at=NOW,
    )
    staging = staging_path.read_text(encoding="utf-8")

    assert report["records_written"] == 1
    assert '"claim_tags": [' in staging
    assert '"incident_date"' in staging
    assert '"location"' in staging
    assert '"related_source_ids": [' in staging


def test_archival_import_reports_rejected_rows_without_writing_article_bodies(tmp_path):
    input_path = tmp_path / "bad_archival_sources.json"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    input_path.write_text(
        '[{"archival_source_id":"trove:article:BAD","capture_method":"trove_api",'
        '"full_article_text":"Do not store this."}]\n',
        encoding="utf-8",
    )

    report = import_archival_sources(
        input_path,
        staging_path=staging_path,
        report_path=report_path,
        imported_at=NOW,
    )
    staging = staging_path.read_text(encoding="utf-8")

    assert report["records_written"] == 0
    assert report["rejected_rows"] == 1
    assert "full article text" in report["errors"][0]["error"]
    assert '"records": []' in staging
    assert "Do not store this." not in staging


def test_archival_tracker_cli_returns_nonzero_when_rows_are_rejected(tmp_path):
    good_input = tmp_path / "good.json"
    good_staging = tmp_path / "good_staging.json"
    good_report = tmp_path / "good_report.json"
    good_input.write_text(
        '{"archival_source_id":"trove:article:SYN-1901","source_platform":"trove",'
        '"source_kind":"newspaper_article","citation":"Synthetic citation."}\n',
        encoding="utf-8",
    )

    assert main(["--input", str(good_input), "--staging", str(good_staging), "--report", str(good_report)]) == 0

    bad_input = tmp_path / "bad.json"
    bad_staging = tmp_path / "bad_staging.json"
    bad_report = tmp_path / "bad_report.json"
    bad_input.write_text(
        '{"archival_source_id":"trove:article:BAD","capture_method":"web_scrape"}\n',
        encoding="utf-8",
    )

    assert main(["--input", str(bad_input), "--staging", str(bad_staging), "--report", str(bad_report)]) == 1


def test_archival_import_can_persist_metadata_records_to_internal_mongo(tmp_path):
    input_path = tmp_path / "archival_sources.json"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    fake_db = FakeMongoDatabase()
    input_path.write_text(
        '[{"archival_source_id":"trove:article:SYN-1901","source_platform":"trove",'
        '"source_kind":"newspaper_article","citation":"Synthetic citation.",'
        '"public_citation_allowed":true,"article_url":"https://trove.example.invalid/article/SYN-1901"}]\n',
        encoding="utf-8",
    )

    report = import_archival_sources(
        input_path,
        staging_path=staging_path,
        report_path=report_path,
        imported_at=NOW,
        mongo_database=fake_db,
    )
    source_collection = fake_db[COLLECTIONS["archival_sources"]]
    report_collection = fake_db[COLLECTIONS["archival_import_reports"]]
    persisted = source_collection.replacements[0]["document"]

    assert report["mongo_persistence"]["records_upserted"] == 1
    assert source_collection.replacements[0]["filter"] == {"archival_source_id": "trove:article:SYN-1901"}
    assert source_collection.replacements[0]["upsert"] is True
    assert persisted["visibility"] == "internal"
    assert persisted["public_visibility"] == "restricted"
    assert persisted["metadata_only"] is True
    assert persisted["article_body_stored"] is False
    assert persisted["side_effects"]["creates_public_feed_entries"] is False
    assert report_collection.inserted[0]["visibility"] == "internal"
    assert report_collection.inserted[0]["rejected_rows"] == 0


def test_archival_mongo_import_reports_rejected_rows_without_persisting_article_text(tmp_path):
    input_path = tmp_path / "bad_archival_sources.json"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    fake_db = FakeMongoDatabase()
    input_path.write_text(
        '[{"archival_source_id":"trove:article:BAD","capture_method":"trove_api",'
        '"full_article_text":"Do not store this."}]\n',
        encoding="utf-8",
    )

    report = import_archival_sources(
        input_path,
        staging_path=staging_path,
        report_path=report_path,
        imported_at=NOW,
        mongo_database=fake_db,
    )
    source_collection = fake_db[COLLECTIONS["archival_sources"]]
    report_collection = fake_db[COLLECTIONS["archival_import_reports"]]

    assert report["mongo_persistence"]["records_upserted"] == 0
    assert source_collection.replacements == []
    assert report_collection.inserted[0]["rejected_rows"] == 1
    assert "Do not store this." not in str(report_collection.inserted[0])


def test_archival_tracker_cli_can_opt_into_mongo_persistence(tmp_path, monkeypatch):
    input_path = tmp_path / "archival_sources.json"
    staging_path = tmp_path / "staging.json"
    report_path = tmp_path / "report.json"
    fake_db = FakeMongoDatabase()
    indexed = {}
    input_path.write_text(
        '{"archival_source_id":"trove:article:SYN-1901","source_platform":"trove",'
        '"source_kind":"newspaper_article","citation":"Synthetic citation."}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr("app.mongodb.get_database", lambda: fake_db)
    monkeypatch.setattr("app.mongodb.ensure_archival_tracker_indexes", lambda db: indexed.setdefault("db", db))

    assert main(["--input", str(input_path), "--staging", str(staging_path), "--report", str(report_path), "--mongo"]) == 0
    assert indexed["db"] is fake_db
    assert len(fake_db[COLLECTIONS["archival_sources"]].replacements) == 1
