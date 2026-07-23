from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


REGISTRY_VERSION = "phase_26b_v1"

SPECIES_UNCONFIRMED_PUBLIC_NOTE = (
    "Species was not officially confirmed in public records. AI1SAD preserves the uncertainty and does not publish "
    "speculative species attribution where doing so could encourage retaliation or distort the source record."
)

SOURCE_TYPES = {
    "gsaf_row",
    "isaf_reference",
    "archival_newspaper",
    "trove_metadata",
    "state_library_record",
    "government_report",
    "coroner_or_inquest",
    "surf_lifesaving_record",
    "vic_hislop_corpus",
    "interview",
    "media_report",
    "scientific_paper",
    "eyewitness_statement",
    "local_authority",
    "unknown",
}

BEHAVIORAL_HYPOTHESES = {
    "attempted_predation_event",
    "predatory_probe",
    "territorial_displacement",
    "competitive_food_response",
    "scavenging_context",
    "accidental_contact",
    "mistaken_identity_candidate",
    "defensive_response",
    "investigative_contact",
    "object_contact_or_investigative_bite",
    "unknown_insufficient_evidence",
}

BEHAVIORAL_CONFIDENCE_VALUES = {
    "unknown",
    "weak",
    "plausible",
    "probable",
    "corroborated",
    "disputed",
    "contradicted",
}

PRIMARY_CONFIDENCE_VALUES = {"weak", "plausible", "probable", "corroborated"}
QUESTIONABLE_SOURCE_CONFIDENCE = {"unknown", "unreviewed", "unsupported", "contradicted"}

OFFICIAL_SPECIES_STATUSES = {
    "confirmed_public",
    "confirmed_not_publicly_disclosed",
    "unconfirmed",
    "disputed",
    "unknown",
    "not_applicable",
}

INTERNAL_SPECIES_CLAIM_STATUSES = {
    "inferred",
    "analyst_hypothesis",
    "source_claimed",
    "official_confirmed_private",
    "disputed",
    "rejected",
}

SPECIES_HYPOTHESIS_VISIBILITIES = {
    "internal_review_only",
    "public_safe",
    "restricted",
    "suppressed_for_retaliation_risk",
}

SPECIES_DISCLOSURE_RISKS = {"none", "low", "moderate", "high", "unknown"}
SPECULATIVE_SPECIES_SUPPRESSION_RISKS = {"moderate", "high"}

CONFLICT_TYPES = {
    "species_disagreement",
    "date_disagreement",
    "location_disagreement",
    "fatality_disagreement",
    "injury_disagreement",
    "behavioral_interpretation_disagreement",
    "source_reliability_disagreement",
    "species_disclosure_disagreement",
}

SIDE_EFFECTS = {
    "creates_warnings": False,
    "creates_alerts": False,
    "creates_public_feed_entries": False,
    "creates_replay_facts": False,
    "creates_drone_observations": False,
    "alters_scoring": False,
    "alters_replay": False,
}


class SourceLink(BaseModel):
    source_id: str
    source_type: str = "unknown"
    source_name: str | None = None
    source_ref: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    source_title: str | None = None
    source_rights_note: str | None = None
    source_confidence: str = "unknown"
    linked_claims: list[str] = Field(default_factory=list)
    quote_excerpt_allowed: bool = False
    quote_excerpt: str | None = None
    public_citation_allowed: bool = False
    full_quote_private_only: str | None = None
    full_copyrighted_article_text: str | None = None
    private_contact_or_source_details: str | None = None
    private_notes: str | None = None


class BehavioralHypothesis(BaseModel):
    hypothesis: str
    confidence: str = "unknown"
    source_ids: list[str] = Field(default_factory=list)
    rationale: str | None = None
    analyst_notes_private: str | None = None


class SourceConflict(BaseModel):
    conflict_id: str
    conflict_type: str
    summary: str
    sources_in_conflict: list[str] = Field(default_factory=list)
    current_resolution: str = "unresolved"
    resolution_confidence: str = "unknown"
    public_summary_allowed: bool = False
    analyst_notes_private: str | None = None


class InternalSpeciesHypothesis(BaseModel):
    species_common_name: str | None = None
    species_scientific_name: str | None = None
    claim_status: str = "analyst_hypothesis"
    confidence: str = "unknown"
    basis: str | None = None
    limitations: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    visibility: str = "internal_review_only"
    analyst_notes_private: str | None = None


class SpeciesClaim(BaseModel):
    species_raw: str | None = None
    normalized_species: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    confidence: str = "unknown"


class SharkSizeClaim(BaseModel):
    size_raw: str | None = None
    size_meters: float | None = None
    source_ids: list[str] = Field(default_factory=list)
    confidence: str = "unknown"


class IncidentRegistryRecord(BaseModel):
    ai1sad_case_id: str
    registry_version: str = REGISTRY_VERSION
    created_at: datetime
    updated_at: datetime
    review_status: str = "unreviewed"
    public_visibility: Literal["private", "restricted", "public"] = "private"
    incident_date_raw: str | None = None
    incident_date_normalized: str | None = None
    incident_time_raw: str | None = None
    country: str | None = None
    region: str | None = None
    area: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    coordinate_confidence: str = "unknown"
    water_body: str | None = None
    activity: str | None = None
    victim_context: str | None = None
    human_group_context: str | None = None
    injury_summary: str | None = None
    injury_severity: str | None = None
    fatality: bool | None = None
    body_recovered: bool | None = None
    consumption_evidence: str | None = None
    official_species_status: str = "unknown"
    official_species_name: str | None = None
    official_species_source_id: str | None = None
    official_species_public_note: str | None = None
    species_claims: list[SpeciesClaim] = Field(default_factory=list)
    internal_species_hypotheses: list[InternalSpeciesHypothesis] = Field(default_factory=list)
    species_disclosure_risk: str = "unknown"
    shark_size_claims: list[SharkSizeClaim] = Field(default_factory=list)
    source_links: list[SourceLink] = Field(default_factory=list)
    behavioral_hypotheses: list[BehavioralHypothesis] = Field(default_factory=list)
    primary_behavioral_hypothesis: str = "unknown_insufficient_evidence"
    behavioral_confidence: str = "unknown"
    alternative_hypotheses: list[str] = Field(default_factory=list)
    rejected_hypotheses: list[str] = Field(default_factory=list)
    source_conflicts: list[SourceConflict] = Field(default_factory=list)
    public_summary: str | None = None
    analyst_notes_private: str | None = None
    provenance_notes: list[str] = Field(default_factory=list)
    normalization_warnings: list[str] = Field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_registry_record(payload: dict[str, Any], *, now: datetime | None = None) -> IncidentRegistryRecord:
    timestamp = now or utc_now()
    data = dict(payload)
    data.setdefault("created_at", timestamp)
    data.setdefault("updated_at", timestamp)
    data.setdefault("registry_version", REGISTRY_VERSION)
    data["source_links"] = [_coerce_source_link(item) for item in data.get("source_links", [])]
    data["species_claims"] = [_coerce_species_claim(item) for item in data.get("species_claims", [])]
    data["internal_species_hypotheses"] = [
        _coerce_internal_species_hypothesis(item) for item in data.get("internal_species_hypotheses", [])
    ]
    data["shark_size_claims"] = [_coerce_shark_size_claim(item) for item in data.get("shark_size_claims", [])]
    _normalize_official_species_fields(data)
    data["behavioral_hypotheses"] = [_coerce_behavioral_hypothesis(item) for item in data.get("behavioral_hypotheses", [])]
    data["source_conflicts"] = [_coerce_source_conflict(item) for item in data.get("source_conflicts", [])]
    data["primary_behavioral_hypothesis"], data["behavioral_confidence"] = select_primary_behavioral_hypothesis(data)
    return IncidentRegistryRecord(**data)


def source_link_from_gsaf_record(record: dict[str, Any]) -> SourceLink:
    return SourceLink(
        source_id=f"gsaf:{record.get('match_key') or record.get('source_case_number') or 'unknown'}",
        source_type="gsaf_row",
        source_name="GSAF",
        source_ref=str(record.get("source_case_number") or ""),
        source_date=str(record.get("source_date_raw") or ""),
        source_title=None,
        source_rights_note="Local/manual GSAF staging reference; raw row is not public output.",
        source_confidence="weak" if record.get("ai1sad_behavior_confidence") != "unknown" else "unknown",
        linked_claims=[
            claim
            for claim in (
                record.get("ai1sad_incident_type_candidate"),
                record.get("ai1sad_behavioral_hypothesis_candidate"),
            )
            if claim
        ],
        public_citation_allowed=False,
        private_notes=f"source_file={record.get('source_file')} row={record.get('source_row_number')}",
    )


def public_safe_registry_output(record: IncidentRegistryRecord) -> dict[str, Any]:
    safe_sources = [_public_source_link(source) for source in record.source_links if source.public_citation_allowed]
    safe_species_hypotheses = _public_internal_species_hypotheses(record)
    safe_hypotheses = [
        {
            "hypothesis": item.hypothesis,
            "confidence": item.confidence,
            "source_ids": item.source_ids,
            "rationale": item.rationale,
        }
        for item in record.behavioral_hypotheses
        if item.hypothesis != "unknown_insufficient_evidence" or item.confidence != "unknown"
    ]
    safe_conflicts = [
        {
            "conflict_id": conflict.conflict_id,
            "conflict_type": conflict.conflict_type,
            "summary": conflict.summary,
            "sources_in_conflict": conflict.sources_in_conflict,
            "current_resolution": conflict.current_resolution,
            "resolution_confidence": conflict.resolution_confidence,
        }
        for conflict in record.source_conflicts
        if conflict.public_summary_allowed
    ]
    return {
        "ai1sad_case_id": record.ai1sad_case_id,
        "registry_version": record.registry_version,
        "review_status": record.review_status,
        "public_visibility": record.public_visibility,
        "incident_date_raw": record.incident_date_raw,
        "incident_date_normalized": record.incident_date_normalized,
        "country": record.country,
        "region": record.region,
        "area": record.area,
        "location": record.location,
        "coordinate_confidence": record.coordinate_confidence,
        "activity": record.activity,
        "injury_summary": record.injury_summary,
        "injury_severity": record.injury_severity,
        "fatality": record.fatality,
        "official_species_status": record.official_species_status,
        "official_species_name": record.official_species_name if record.official_species_status == "confirmed_public" else None,
        "official_species_source_id": (
            record.official_species_source_id if record.official_species_status == "confirmed_public" else None
        ),
        "official_species_public_note": _public_species_note(record),
        "internal_species_hypotheses": safe_species_hypotheses,
        "shark_size_claims": [claim.model_dump() for claim in record.shark_size_claims],
        "public_summary": record.public_summary,
        "source_citations": safe_sources,
        "behavioral_hypotheses": safe_hypotheses,
        "primary_behavioral_hypothesis": record.primary_behavioral_hypothesis,
        "behavioral_confidence": record.behavioral_confidence,
        "alternative_hypotheses": record.alternative_hypotheses,
        "normalization_warnings": record.normalization_warnings,
        "source_conflicts": safe_conflicts,
    }


def registry_side_effects() -> dict[str, bool]:
    return dict(SIDE_EFFECTS)


def _coerce_source_link(item: SourceLink | dict[str, Any]) -> SourceLink:
    source = item if isinstance(item, SourceLink) else SourceLink(**item)
    if source.source_type not in SOURCE_TYPES:
        return source.model_copy(update={"source_type": "unknown"})
    return source


def _coerce_species_claim(item: SpeciesClaim | dict[str, Any]) -> SpeciesClaim:
    claim = item if isinstance(item, SpeciesClaim) else SpeciesClaim(**item)
    if claim.confidence not in BEHAVIORAL_CONFIDENCE_VALUES:
        return claim.model_copy(update={"confidence": "unknown"})
    return claim


def _coerce_internal_species_hypothesis(
    item: InternalSpeciesHypothesis | dict[str, Any],
) -> InternalSpeciesHypothesis:
    hypothesis = item if isinstance(item, InternalSpeciesHypothesis) else InternalSpeciesHypothesis(**item)
    updates: dict[str, Any] = {}
    if hypothesis.claim_status not in INTERNAL_SPECIES_CLAIM_STATUSES:
        updates["claim_status"] = "analyst_hypothesis"
    if hypothesis.confidence not in BEHAVIORAL_CONFIDENCE_VALUES:
        updates["confidence"] = "unknown"
    if hypothesis.visibility not in SPECIES_HYPOTHESIS_VISIBILITIES:
        updates["visibility"] = "internal_review_only"
    return hypothesis.model_copy(update=updates) if updates else hypothesis


def _coerce_shark_size_claim(item: SharkSizeClaim | dict[str, Any]) -> SharkSizeClaim:
    claim = item if isinstance(item, SharkSizeClaim) else SharkSizeClaim(**item)
    if claim.confidence not in BEHAVIORAL_CONFIDENCE_VALUES:
        return claim.model_copy(update={"confidence": "unknown"})
    return claim


def _coerce_behavioral_hypothesis(item: BehavioralHypothesis | dict[str, Any]) -> BehavioralHypothesis:
    hypothesis = item if isinstance(item, BehavioralHypothesis) else BehavioralHypothesis(**item)
    updates: dict[str, Any] = {}
    if hypothesis.hypothesis not in BEHAVIORAL_HYPOTHESES:
        updates["hypothesis"] = "unknown_insufficient_evidence"
    if hypothesis.confidence not in BEHAVIORAL_CONFIDENCE_VALUES:
        updates["confidence"] = "unknown"
    return hypothesis.model_copy(update=updates) if updates else hypothesis


def _coerce_source_conflict(item: SourceConflict | dict[str, Any]) -> SourceConflict:
    conflict = item if isinstance(item, SourceConflict) else SourceConflict(**item)
    if conflict.conflict_type not in CONFLICT_TYPES:
        return conflict.model_copy(update={"conflict_type": "source_reliability_disagreement"})
    return conflict


def _normalize_official_species_fields(data: dict[str, Any]) -> None:
    status = str(data.get("official_species_status") or "unknown")
    risk = str(data.get("species_disclosure_risk") or "unknown")
    warnings = list(data.get("normalization_warnings", []))

    if status not in OFFICIAL_SPECIES_STATUSES:
        status = "unknown"
        warnings.append("official_species_status_invalid")
    if risk not in SPECIES_DISCLOSURE_RISKS:
        risk = "unknown"
        warnings.append("species_disclosure_risk_invalid")

    official_name = data.get("official_species_name")
    official_source_id = data.get("official_species_source_id")
    if status == "confirmed_public" and (not official_name or not official_source_id):
        status = "unconfirmed"
        official_name = None
        official_source_id = None
        warnings.append("official_species_public_confirmation_missing")
    elif status in {"unconfirmed", "unknown", "not_applicable"}:
        official_name = None
        official_source_id = None

    data["official_species_status"] = status
    data["official_species_name"] = official_name
    data["official_species_source_id"] = official_source_id
    data["species_disclosure_risk"] = risk
    if status != "confirmed_public" and not data.get("official_species_public_note"):
        data["official_species_public_note"] = SPECIES_UNCONFIRMED_PUBLIC_NOTE
    data["normalization_warnings"] = warnings


def select_primary_behavioral_hypothesis(payload: dict[str, Any]) -> tuple[str, str]:
    if questionable_evidence(payload):
        return "unknown_insufficient_evidence", "unknown"

    requested_primary = str(payload.get("primary_behavioral_hypothesis") or "unknown_insufficient_evidence")
    requested_confidence = str(payload.get("behavioral_confidence") or "unknown")
    if requested_primary in BEHAVIORAL_HYPOTHESES and requested_confidence in PRIMARY_CONFIDENCE_VALUES:
        return requested_primary, requested_confidence

    best = _best_selectable_hypothesis(payload.get("behavioral_hypotheses", []))
    if best:
        return best.hypothesis, best.confidence
    return "unknown_insufficient_evidence", "unknown"


def questionable_evidence(payload: dict[str, Any]) -> bool:
    warnings = {str(item).lower() for item in payload.get("normalization_warnings", [])}
    if any("questionable" in item or "unconfirmed" in item or "unsupported" in item for item in warnings):
        return True
    source_links = [_coerce_source_link(item) for item in payload.get("source_links", [])]
    if not source_links:
        return True
    selectable_sources = [
        source
        for source in source_links
        if str(source.source_confidence).lower() not in QUESTIONABLE_SOURCE_CONFIDENCE
    ]
    return not selectable_sources


def _best_selectable_hypothesis(items: list[BehavioralHypothesis | dict[str, Any]]) -> BehavioralHypothesis | None:
    rank = {"weak": 1, "plausible": 2, "probable": 3, "corroborated": 4}
    hypotheses = [_coerce_behavioral_hypothesis(item) for item in items]
    candidates = [item for item in hypotheses if item.confidence in PRIMARY_CONFIDENCE_VALUES]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: rank[item.confidence], reverse=True)[0]


def _public_species_note(record: IncidentRegistryRecord) -> str | None:
    if record.official_species_status == "confirmed_public":
        return record.official_species_public_note
    return record.official_species_public_note or SPECIES_UNCONFIRMED_PUBLIC_NOTE


def _public_internal_species_hypotheses(record: IncidentRegistryRecord) -> list[dict[str, Any]]:
    if record.species_disclosure_risk in SPECULATIVE_SPECIES_SUPPRESSION_RISKS:
        return []
    safe_hypotheses = []
    for hypothesis in record.internal_species_hypotheses:
        if hypothesis.visibility != "public_safe":
            continue
        if hypothesis.claim_status == "official_confirmed_private":
            continue
        payload = {
            "species_common_name": hypothesis.species_common_name,
            "species_scientific_name": hypothesis.species_scientific_name,
            "claim_status": hypothesis.claim_status,
            "confidence": hypothesis.confidence,
            "basis": hypothesis.basis,
            "limitations": hypothesis.limitations,
            "source_ids": hypothesis.source_ids,
            "visibility": hypothesis.visibility,
        }
        safe_hypotheses.append({key: value for key, value in payload.items() if value not in (None, [], "")})
    return safe_hypotheses


def _public_source_link(source: SourceLink) -> dict[str, Any]:
    payload = {
        "source_id": source.source_id,
        "source_type": source.source_type,
        "source_name": source.source_name,
        "source_ref": source.source_ref,
        "source_url": source.source_url,
        "source_date": source.source_date,
        "source_title": source.source_title,
        "source_rights_note": source.source_rights_note,
        "source_confidence": source.source_confidence,
        "linked_claims": source.linked_claims,
        "public_citation_allowed": source.public_citation_allowed,
    }
    if source.quote_excerpt_allowed:
        payload["quote_excerpt"] = source.quote_excerpt
    return {key: value for key, value in payload.items() if value not in (None, [], "")}
