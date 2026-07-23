from __future__ import annotations

from datetime import datetime, timezone

from app.services.incident_registry import (
    BEHAVIORAL_HYPOTHESES,
    CONFLICT_TYPES,
    INTERNAL_SPECIES_CLAIM_STATUSES,
    OFFICIAL_SPECIES_STATUSES,
    REGISTRY_VERSION,
    SOURCE_TYPES,
    SPECIES_DISCLOSURE_RISKS,
    SPECIES_HYPOTHESIS_VISIBILITIES,
    SPECIES_UNCONFIRMED_PUBLIC_NOTE,
    create_registry_record,
    public_safe_registry_output,
    registry_side_effects,
    source_link_from_gsaf_record,
)


NOW = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)


def synthetic_case_payload() -> dict:
    return {
        "ai1sad_case_id": "AI1SAD-SYN-0001",
        "review_status": "analyst_review",
        "public_visibility": "public",
        "incident_date_raw": "June 1901",
        "incident_date_normalized": None,
        "incident_time_raw": "afternoon",
        "country": "Australia",
        "region": "Queensland",
        "area": "Synthetic Coast",
        "location": "Example Beach",
        "latitude": -25.0,
        "longitude": 153.0,
        "coordinate_confidence": "approximate_region",
        "water_body": "Coral Sea",
        "activity": "bathing",
        "victim_context": "name withheld",
        "human_group_context": "nearshore public beach",
        "injury_summary": "Synthetic injury summary",
        "injury_severity": "serious",
        "fatality": False,
        "body_recovered": True,
        "consumption_evidence": "none_reported",
        "official_species_status": "unknown",
        "official_species_name": None,
        "official_species_source_id": None,
        "official_species_public_note": None,
        "species_disclosure_risk": "unknown",
        "species_claims": [
            {
                "species_raw": "large shark",
                "normalized_species": None,
                "source_ids": ["gsaf:case:SYN.1901.01"],
                "confidence": "weak",
            }
        ],
        "internal_species_hypotheses": [
            {
                "species_common_name": "large shark candidate",
                "species_scientific_name": None,
                "claim_status": "analyst_hypothesis",
                "confidence": "weak",
                "basis": "Synthetic analyst-only species note.",
                "limitations": "Not publicly confirmed.",
                "source_ids": ["gsaf:case:SYN.1901.01"],
                "visibility": "internal_review_only",
                "analyst_notes_private": "candidate species remains internal",
            }
        ],
        "shark_size_claims": [
            {
                "size_raw": "about 8 feet",
                "size_meters": None,
                "source_ids": ["archive:trove:SYN-1901"],
                "confidence": "weak",
            }
        ],
        "source_links": [
            {
                "source_id": "gsaf:case:SYN.1901.01",
                "source_type": "gsaf_row",
                "source_name": "GSAF synthetic fixture",
                "source_ref": "SYN.1901.01",
                "source_date": "1901",
                "source_rights_note": "Synthetic test metadata only; raw upstream row not public.",
                "source_confidence": "weak",
                "linked_claims": ["date", "location", "injury"],
                "public_citation_allowed": False,
                "private_notes": "row notes stay private",
            },
            {
                "source_id": "archive:trove:SYN-1901",
                "source_type": "archival_newspaper",
                "source_name": "Synthetic Gazette",
                "source_ref": "p. 2",
                "source_url": "https://example.invalid/archive/synthetic",
                "source_date": "1901-06-02",
                "source_title": "Synthetic beach incident",
                "source_rights_note": "Citation only; article body not redistributed.",
                "source_confidence": "plausible",
                "linked_claims": ["activity", "injury"],
                "quote_excerpt_allowed": True,
                "quote_excerpt": "Short rights-reviewed synthetic excerpt.",
                "public_citation_allowed": True,
                "full_copyrighted_article_text": "FULL ARTICLE TEXT MUST STAY PRIVATE",
                "private_notes": "OCR needs analyst review",
            },
            {
                "source_id": "hislop:claim:SYN-CLAIM",
                "source_type": "vic_hislop_corpus",
                "source_name": "Synthetic Hislop corpus note",
                "source_ref": "claim card",
                "source_rights_note": "Synthetic claim metadata only.",
                "source_confidence": "disputed",
                "linked_claims": ["behavioral interpretation"],
                "public_citation_allowed": True,
                "full_quote_private_only": "FULL PRIVATE QUOTE MUST STAY PRIVATE",
                "private_notes": "claim requires corroboration",
            },
        ],
        "behavioral_hypotheses": [
            {
                "hypothesis": "investigative_contact",
                "confidence": "weak",
                "source_ids": ["archive:trove:SYN-1901"],
                "rationale": "Synthetic archival metadata suggests a nonfatal exploratory contact.",
                "analyst_notes_private": "not public",
            },
            {
                "hypothesis": "mistaken_identity_candidate",
                "confidence": "weak",
                "source_ids": ["hislop:claim:SYN-CLAIM"],
                "rationale": "A disputed corpus claim is retained only as an alternative.",
            },
        ],
        "alternative_hypotheses": ["mistaken_identity_candidate"],
        "rejected_hypotheses": ["confirmed_shark_intent"],
        "source_conflicts": [
            {
                "conflict_id": "conflict:species:SYN-1901",
                "conflict_type": "species_disagreement",
                "summary": "Synthetic sources disagree on species certainty.",
                "sources_in_conflict": ["gsaf:case:SYN.1901.01", "hislop:claim:SYN-CLAIM"],
                "current_resolution": "retain_uncertain_species",
                "resolution_confidence": "weak",
                "public_summary_allowed": True,
                "analyst_notes_private": "detailed conflict notes stay private",
            }
        ],
        "public_summary": "Synthetic public-safe case summary.",
        "analyst_notes_private": "internal analyst note",
        "provenance_notes": ["synthetic test case only"],
        "normalization_warnings": ["date_vague_preserved"],
    }


def synthetic_waiehu_species_payload() -> dict:
    return {
        **synthetic_case_payload(),
        "ai1sad_case_id": "AI1SAD-SYN-WAIEHU-0001",
        "country": "United States",
        "region": "Hawaii",
        "area": "Maui",
        "location": "Waiehu",
        "water_body": "Pacific Ocean",
        "activity": "surfing",
        "victim_context": "adult male surfer",
        "human_group_context": "nearshore surf zone",
        "injury_summary": "Synthetic severe below-knee leg injury in turbid shallow water.",
        "injury_severity": "severe",
        "official_species_status": "unconfirmed",
        "official_species_name": None,
        "official_species_source_id": None,
        "official_species_public_note": None,
        "species_disclosure_risk": "moderate",
        "species_claims": [
            {
                "species_raw": "species not confirmed in public record",
                "normalized_species": None,
                "source_ids": ["source:local:waiehu-synthetic"],
                "confidence": "unknown",
            }
        ],
        "internal_species_hypotheses": [
            {
                "species_common_name": "tiger shark",
                "species_scientific_name": "Galeocerdo cuvier",
                "claim_status": "analyst_hypothesis",
                "confidence": "plausible",
                "basis": "Synthetic internal hypothesis based on turbid water, shallow depth, and regional ecology.",
                "limitations": "No public official species confirmation.",
                "source_ids": ["source:local:waiehu-synthetic"],
                "visibility": "internal_review_only",
                "analyst_notes_private": "retaliation-sensitive candidate note",
            }
        ],
        "source_links": [
            {
                "source_id": "source:local:waiehu-synthetic",
                "source_type": "local_authority",
                "source_name": "Synthetic local authority metadata",
                "source_ref": "WAIEHU-SYN",
                "source_date": "2026-01-01",
                "source_title": "Synthetic Waiehu incident metadata",
                "source_rights_note": "Synthetic citation metadata only; no article body.",
                "source_confidence": "plausible",
                "linked_claims": ["location", "injury", "species unconfirmed"],
                "public_citation_allowed": True,
                "private_notes": "retaliation-sensitive source note",
            }
        ],
        "behavioral_hypotheses": [
            {
                "hypothesis": "unknown_insufficient_evidence",
                "confidence": "unknown",
                "source_ids": ["source:local:waiehu-synthetic"],
            }
        ],
        "source_conflicts": [
            {
                "conflict_id": "conflict:species-disclosure:WAIEHU-SYN",
                "conflict_type": "species_disclosure_disagreement",
                "summary": "Synthetic public records do not disclose a species while internal review retains a hypothesis.",
                "sources_in_conflict": ["source:local:waiehu-synthetic"],
                "current_resolution": "retain_internal_hypothesis_suppress_public_species",
                "resolution_confidence": "plausible",
                "public_summary_allowed": True,
                "analyst_notes_private": "private species-disclosure decision note",
            }
        ],
        "public_summary": "Synthetic Waiehu/Maui surfer injury summary. Species was not publicly confirmed.",
        "analyst_notes_private": "Retain internal species candidate for review only.",
        "normalization_warnings": ["species_public_confirmation_absent"],
    }


def test_valid_registry_case_creation_with_multiple_source_links():
    record = create_registry_record(synthetic_case_payload(), now=NOW)

    assert record.registry_version == REGISTRY_VERSION
    assert record.created_at == NOW
    assert record.updated_at == NOW
    assert record.ai1sad_case_id == "AI1SAD-SYN-0001"
    assert len(record.source_links) == 3
    assert {source.source_type for source in record.source_links} >= {
        "gsaf_row",
        "archival_newspaper",
        "vic_hislop_corpus",
    }
    assert record.coordinate_confidence == "approximate_region"
    assert record.normalization_warnings == ["date_vague_preserved"]
    assert record.official_species_status == "unknown"
    assert record.internal_species_hypotheses[0].species_common_name == "large shark candidate"


def test_value_sets_cover_required_phase_26b_values():
    assert {
        "gsaf_row",
        "archival_newspaper",
        "trove_metadata",
        "vic_hislop_corpus",
        "coroner_or_inquest",
        "local_authority",
        "unknown",
    } <= SOURCE_TYPES
    assert {
        "attempted_predation_event",
        "predatory_probe",
        "competitive_food_response",
        "scavenging_context",
        "mistaken_identity_candidate",
        "defensive_response",
        "unknown_insufficient_evidence",
    } <= BEHAVIORAL_HYPOTHESES
    assert {
        "confirmed_public",
        "confirmed_not_publicly_disclosed",
        "unconfirmed",
        "disputed",
        "unknown",
        "not_applicable",
    } <= OFFICIAL_SPECIES_STATUSES
    assert {"inferred", "analyst_hypothesis", "source_claimed", "official_confirmed_private", "rejected"} <= (
        INTERNAL_SPECIES_CLAIM_STATUSES
    )
    assert {"internal_review_only", "public_safe", "restricted", "suppressed_for_retaliation_risk"} <= (
        SPECIES_HYPOTHESIS_VISIBILITIES
    )
    assert {"none", "low", "moderate", "high", "unknown"} <= SPECIES_DISCLOSURE_RISKS
    assert "species_disclosure_disagreement" in CONFLICT_TYPES


def test_gsaf_source_link_is_preserved_as_source_not_final_truth():
    staged_row = {
        "match_key": "case:SYN.1901.01",
        "source_case_number": "SYN.1901.01",
        "source_date_raw": "June 1901",
        "source_file": "synthetic_gsaf.csv",
        "source_row_number": 2,
        "ai1sad_incident_type_candidate": "human_shark_interaction_candidate",
        "ai1sad_behavioral_hypothesis_candidate": "unknown_insufficient_evidence",
        "ai1sad_behavior_confidence": "unknown",
    }

    source = source_link_from_gsaf_record(staged_row)

    assert source.source_type == "gsaf_row"
    assert source.source_name == "GSAF"
    assert source.source_ref == "SYN.1901.01"
    assert source.public_citation_allowed is False
    assert "unknown_insufficient_evidence" in source.linked_claims


def test_no_default_mistaken_identity_and_unknown_for_questionable_evidence():
    payload = {
        **synthetic_case_payload(),
        "source_links": [
            {
                "source_id": "source:questionable",
                "source_type": "media_report",
                "source_name": "Synthetic unconfirmed report",
                "source_confidence": "unknown",
            }
        ],
        "behavioral_hypotheses": [
            {
                "hypothesis": "mistaken_identity_candidate",
                "confidence": "plausible",
                "source_ids": ["source:questionable"],
            }
        ],
        "primary_behavioral_hypothesis": "mistaken_identity_candidate",
        "behavioral_confidence": "plausible",
        "normalization_warnings": ["source_unconfirmed_behavior_unknown"],
    }

    record = create_registry_record(payload, now=NOW)

    assert record.primary_behavioral_hypothesis == "unknown_insufficient_evidence"
    assert record.behavioral_confidence == "unknown"


def test_multiple_competing_hypotheses_selects_only_supported_primary():
    payload = {
        **synthetic_case_payload(),
        "behavioral_hypotheses": [
            {
                "hypothesis": "competitive_food_response",
                "confidence": "plausible",
                "source_ids": ["archive:trove:SYN-1901"],
            },
            {
                "hypothesis": "mistaken_identity_candidate",
                "confidence": "weak",
                "source_ids": ["hislop:claim:SYN-CLAIM"],
            },
        ],
        "primary_behavioral_hypothesis": "mistaken_identity_candidate",
        "behavioral_confidence": "unknown",
    }

    record = create_registry_record(payload, now=NOW)

    assert len(record.behavioral_hypotheses) == 2
    assert record.primary_behavioral_hypothesis == "competitive_food_response"
    assert record.behavioral_confidence == "plausible"
    assert "mistaken_identity_candidate" in record.alternative_hypotheses


def test_conflict_tracking_between_sources_is_preserved():
    record = create_registry_record(synthetic_case_payload(), now=NOW)
    conflict = record.source_conflicts[0]

    assert conflict.conflict_type == "species_disagreement"
    assert conflict.sources_in_conflict == ["gsaf:case:SYN.1901.01", "hislop:claim:SYN-CLAIM"]
    assert conflict.current_resolution == "retain_uncertain_species"
    assert conflict.resolution_confidence == "weak"


def test_public_safe_output_excludes_private_fields_and_copyrighted_text():
    record = create_registry_record(synthetic_case_payload(), now=NOW)
    public = public_safe_registry_output(record)
    rendered = str(public)

    assert public["ai1sad_case_id"] == "AI1SAD-SYN-0001"
    assert public["public_summary"] == "Synthetic public-safe case summary."
    assert [source["source_id"] for source in public["source_citations"]] == [
        "archive:trove:SYN-1901",
        "hislop:claim:SYN-CLAIM",
    ]
    assert "Short rights-reviewed synthetic excerpt." in rendered
    assert "internal analyst note" not in rendered
    assert "row notes stay private" not in rendered
    assert "FULL ARTICLE TEXT MUST STAY PRIVATE" not in rendered
    assert "FULL PRIVATE QUOTE MUST STAY PRIVATE" not in rendered
    assert "detailed conflict notes stay private" not in rendered
    assert "analyst_notes_private" not in rendered
    assert "private_notes" not in rendered
    assert "species_claims" not in public
    assert "large shark candidate" not in rendered


def test_public_safe_output_preserves_safe_warnings_and_public_conflict_summary():
    record = create_registry_record(synthetic_case_payload(), now=NOW)
    public = public_safe_registry_output(record)

    assert public["normalization_warnings"] == ["date_vague_preserved"]
    assert public["source_conflicts"][0]["conflict_id"] == "conflict:species:SYN-1901"
    assert public["source_conflicts"][0]["summary"] == "Synthetic sources disagree on species certainty."


def test_unconfirmed_official_species_keeps_internal_hypothesis_private_by_default():
    record = create_registry_record(synthetic_waiehu_species_payload(), now=NOW)
    public = public_safe_registry_output(record)
    rendered = str(public).lower()

    assert record.official_species_status == "unconfirmed"
    assert record.internal_species_hypotheses[0].species_common_name == "tiger shark"
    assert record.internal_species_hypotheses[0].confidence == "plausible"
    assert public["official_species_status"] == "unconfirmed"
    assert public["official_species_name"] is None
    assert public["official_species_source_id"] is None
    assert public["official_species_public_note"] == SPECIES_UNCONFIRMED_PUBLIC_NOTE
    assert public["internal_species_hypotheses"] == []
    assert "tiger shark" not in rendered
    assert "galeocerdo" not in rendered
    assert "retaliation-sensitive candidate note" not in rendered
    assert "retaliation-sensitive source note" not in rendered
    assert "private species-disclosure decision note" not in rendered
    assert "analyst_notes_private" not in rendered


def test_moderate_or_high_species_disclosure_risk_suppresses_public_safe_species_hypothesis():
    payload = synthetic_waiehu_species_payload()
    payload["species_disclosure_risk"] = "high"
    payload["internal_species_hypotheses"][0]["visibility"] = "public_safe"

    record = create_registry_record(payload, now=NOW)
    public = public_safe_registry_output(record)

    assert record.internal_species_hypotheses[0].visibility == "public_safe"
    assert record.species_disclosure_risk == "high"
    assert public["internal_species_hypotheses"] == []
    assert "tiger shark" not in str(public).lower()


def test_low_species_disclosure_risk_allows_explicit_public_safe_species_hypothesis():
    payload = synthetic_waiehu_species_payload()
    payload["species_disclosure_risk"] = "low"
    payload["internal_species_hypotheses"][0]["claim_status"] = "source_claimed"
    payload["internal_species_hypotheses"][0]["visibility"] = "public_safe"

    record = create_registry_record(payload, now=NOW)
    public = public_safe_registry_output(record)

    assert public["internal_species_hypotheses"] == [
        {
            "species_common_name": "tiger shark",
            "species_scientific_name": "Galeocerdo cuvier",
            "claim_status": "source_claimed",
            "confidence": "plausible",
            "basis": "Synthetic internal hypothesis based on turbid water, shallow depth, and regional ecology.",
            "limitations": "No public official species confirmation.",
            "source_ids": ["source:local:waiehu-synthetic"],
            "visibility": "public_safe",
        }
    ]
    assert "analyst_notes_private" not in str(public)


def test_confirmed_public_species_requires_public_name_and_source_id():
    payload = synthetic_waiehu_species_payload()
    payload["official_species_status"] = "confirmed_public"
    payload["official_species_name"] = "tiger shark"
    payload["official_species_source_id"] = None

    record = create_registry_record(payload, now=NOW)
    public = public_safe_registry_output(record)

    assert record.official_species_status == "unconfirmed"
    assert record.official_species_name is None
    assert "official_species_public_confirmation_missing" in record.normalization_warnings
    assert public["official_species_name"] is None
    assert public["official_species_public_note"] == SPECIES_UNCONFIRMED_PUBLIC_NOTE


def test_registry_records_do_not_create_scoring_replay_feed_or_drone_side_effects():
    record = create_registry_record(synthetic_case_payload(), now=NOW)

    assert record.ai1sad_case_id
    assert registry_side_effects() == {
        "creates_warnings": False,
        "creates_alerts": False,
        "creates_public_feed_entries": False,
        "creates_replay_facts": False,
        "creates_drone_observations": False,
        "alters_scoring": False,
        "alters_replay": False,
    }
