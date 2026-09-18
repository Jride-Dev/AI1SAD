"""Source-linked AI1SAD shark-human incident registry seed cases."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from app.services.incident_registry import IncidentRegistryRecord, create_registry_record


GLENFIELD_BEACH_MEL_ISMAIL_2026_CASE_ID = "AI1SAD-WA-GLENFIELD-BEACH-2026-09-14"


GLENFIELD_BEACH_MEL_ISMAIL_2026: dict[str, Any] = {
    "ai1sad_case_id": GLENFIELD_BEACH_MEL_ISMAIL_2026_CASE_ID,
    "source_case_ids": [
        "abc:2026-09-15:geraldton-shark-attack",
        "abc:2026-09-18:glenfield-beach-rescuer",
        "seven:2026-09-15:glenfield-beach-mel-ismail",
        "geraldton_guardian:2026-09-14:mel-ismail",
        "newscomau:2026-09-14:hero-teens-mel-ismail",
    ],
    "registry_version": "AI1SAD-incident-registry-v1",
    "review_status": "source_review",
    "public_visibility": "restricted",
    "incident_date_raw": "Monday 14 September 2026",
    "incident_date_normalized": "2026-09-14",
    "incident_time_raw": "about 09:45-09:50 local time",
    "incident_time_normalized": None,
    "timezone": "Australia/Perth",
    "country": "Australia",
    "region": "Western Australia",
    "area": "Mid West / Geraldton",
    "location": "Glenfield Beach, north of Geraldton",
    "latitude": None,
    "longitude": None,
    "coordinate_confidence": "named_beach_only",
    "water_body": "Indian Ocean",
    "activity": "surfing",
    "victim_context": "Mel Ismail, 56-year-old Geraldton firefighter and surfer",
    "human_group_context": (
        "Reportedly surfing alone around 40 m offshore; another surfer paddled to "
        "assist and beachgoers helped once the victim was brought to shore."
    ),
    "injury_summary": (
        "Catastrophic right lower-leg injury with subsequent below-shin amputation; "
        "serious but stable condition reported after treatment at Geraldton Health Campus."
    ),
    "injury_severity": "severe",
    "fatality": False,
    "body_recovered": None,
    "consumption_evidence": "none_reported",
    "official_species_status": "unconfirmed",
    "official_species_name": None,
    "official_species_source_id": None,
    "official_species_public_note": (
        "No official shark species identification had been released; WA fisheries/DPIRD "
        "testing of the damaged surfboard was reported as underway."
    ),
    "species_claims": [
        {
            "species_raw": (
                "Unknown shark; fisheries testing of the severely damaged surfboard was "
                "reported as underway to help determine species and size."
            ),
            "normalized_species": None,
            "source_ids": [
                "abc:2026-09-15:geraldton-shark-attack",
                "abc:2026-09-18:glenfield-beach-rescuer",
                "geraldton_guardian:2026-09-14:mel-ismail",
                "newscomau:2026-09-14:hero-teens-mel-ismail",
            ],
            "confidence": "unknown",
            "attribution_notes": "Species was not published as confirmed by official sources.",
        }
    ],
    "internal_species_hypotheses": [],
    "species_disclosure_risk": "moderate",
    "shark_size_claims": [
        {
            "size_raw": (
                "Unknown; damaged surfboard retained by WA fisheries/DPIRD for species "
                "and size examination."
            ),
            "size_meters": None,
            "source_ids": [
                "abc:2026-09-15:geraldton-shark-attack",
                "abc:2026-09-18:glenfield-beach-rescuer",
                "geraldton_guardian:2026-09-14:mel-ismail",
            ],
            "confidence": "unknown",
            "attribution_notes": "No confirmed size was available at registry entry time.",
        }
    ],
    "behavioral_hypotheses": [
        {
            "hypothesis": "unknown_insufficient_evidence",
            "confidence": "unknown",
            "source_ids": [
                "abc:2026-09-15:geraldton-shark-attack",
                "abc:2026-09-18:glenfield-beach-rescuer",
                "seven:2026-09-15:glenfield-beach-mel-ismail",
                "geraldton_guardian:2026-09-14:mel-ismail",
            ],
            "rationale": (
                "Published reporting describes injuries, a damaged surfboard, and rescue "
                "sequence, but does not establish shark intent or event mechanics."
            ),
        },
        {
            "hypothesis": "attempted_predation_event",
            "confidence": "unknown",
            "source_ids": [
                "seven:2026-09-15:glenfield-beach-mel-ismail",
                "newscomau:2026-09-14:hero-teens-mel-ismail",
            ],
            "rationale": (
                "Retained only as a provisional competing hypothesis because of the "
                "catastrophic lower-leg injury and severe board damage; not selected as "
                "primary pending forensic and source review."
            ),
        },
        {
            "hypothesis": "predatory_probe",
            "confidence": "unknown",
            "source_ids": [
                "seven:2026-09-15:glenfield-beach-mel-ismail",
                "geraldton_guardian:2026-09-14:mel-ismail",
            ],
            "rationale": (
                "Retained only as a provisional competing hypothesis while species, size, "
                "and bite mechanics remain unconfirmed."
            ),
        },
    ],
    "primary_behavioral_hypothesis": "unknown_insufficient_evidence",
    "behavioral_confidence": "unknown",
    "alternative_hypotheses": ["attempted_predation_event", "predatory_probe"],
    "rejected_hypotheses": ["confirmed_shark_intent"],
    "source_conflicts": [],
    "source_links": [
        {
            "source_id": "abc:2026-09-15:geraldton-shark-attack",
            "source_type": "media_report",
            "source_name": "ABC News",
            "source_url": "https://www.abc.net.au/news/2026-09-15/geraldton-shark-attack-family-thanks-community-for-support/107155200",
            "source_date": "2026-09-15",
            "source_title": (
                "Family of Geraldton shark attack victim Mel Ismail thankful for "
                "community support"
            ),
            "source_rights_note": (
                "Citation and paraphrase only; copyrighted article body is not redistributed."
            ),
            "source_confidence": "plausible",
            "linked_claims": [
                "identity",
                "location",
                "condition",
                "fisheries_board_testing",
                "species_unconfirmed",
            ],
            "public_citation_allowed": False,
            "private_notes": "Active named-victim incident; suppress public citation metadata for now.",
        },
        {
            "source_id": "abc:2026-09-18:glenfield-beach-rescuer",
            "source_type": "media_report",
            "source_name": "ABC News",
            "source_url": "https://www.abc.net.au/news/2026-09-18/glenfield-beach-geraldton-shark-attack-rescuer/107163870",
            "source_date": "2026-09-18",
            "source_title": "Geraldton shark attack rescuer vows to get back in the water",
            "source_rights_note": (
                "Citation and paraphrase only; copyrighted article body is not redistributed."
            ),
            "source_confidence": "plausible",
            "linked_claims": [
                "rescuer_identity",
                "rescue_sequence",
                "tourniquet",
                "stable_condition",
                "dna_analysis_underway",
                "species_unconfirmed",
            ],
            "public_citation_allowed": False,
            "private_notes": "Active named-victim incident; suppress public citation metadata for now.",
        },
        {
            "source_id": "seven:2026-09-15:glenfield-beach-mel-ismail",
            "source_type": "media_report",
            "source_name": "7NEWS",
            "source_url": "https://7news.com.au/news/glenfield-beach-shark-attack-mel-ismail-undergoes-surgery-family-issues-statement-c-22873621",
            "source_date": "2026-09-15",
            "source_title": (
                "Glenfield Beach shark attack: Mel Ismail undergoes surgery, family "
                "issues statement"
            ),
            "source_rights_note": (
                "Citation and paraphrase only; copyrighted article body is not redistributed."
            ),
            "source_confidence": "plausible",
            "linked_claims": [
                "age",
                "amputation",
                "distance_offshore",
                "rescue_sequence",
                "tourniquet",
            ],
            "public_citation_allowed": False,
            "private_notes": "Active named-victim incident; suppress public citation metadata for now.",
        },
        {
            "source_id": "geraldton_guardian:2026-09-14:mel-ismail",
            "source_type": "media_report",
            "source_name": "Geraldton Guardian",
            "source_url": "https://www.geraldtonguardian.com.au/news/geraldton-guardian/glenfield-beach-shark-attack-man-bitten-confirmed-as-geraldton-surfer-mel-ismail-c-22868392.amp",
            "source_date": "2026-09-14",
            "source_title": (
                "Glenfield Beach shark attack: man bitten confirmed as Geraldton surfer "
                "Mel Ismail"
            ),
            "source_rights_note": (
                "Citation and paraphrase only; copyrighted article body is not redistributed."
            ),
            "source_confidence": "plausible",
            "linked_claims": [
                "identity",
                "time_reported",
                "surfing_alone",
                "rescue_sequence",
                "species_unconfirmed",
                "unknown_size_species",
            ],
            "public_citation_allowed": False,
            "private_notes": "Active named-victim incident; suppress public citation metadata for now.",
        },
        {
            "source_id": "newscomau:2026-09-14:hero-teens-mel-ismail",
            "source_type": "media_report",
            "source_name": "news.com.au",
            "source_url": "https://www.news.com.au/travel/travel-updates/incidents/hero-teens-use-surfboard-ripcord-to-tourniquet-leg-of-shark-attack-victim/news-story/cd277d2585028f36fca44991117f6de5",
            "source_date": "2026-09-14",
            "source_title": "Hero teens use surfboard ripcord to tourniquet leg of shark attack victim",
            "source_rights_note": (
                "Citation and paraphrase only; copyrighted article body is not redistributed."
            ),
            "source_confidence": "plausible",
            "linked_claims": [
                "time",
                "distance_offshore",
                "rescue_sequence",
                "tourniquet",
                "serious_stable",
            ],
            "public_citation_allowed": False,
            "private_notes": "Active named-victim incident; suppress public citation metadata for now.",
        },
    ],
    "public_summary": (
        "On 2026-09-14, a 56-year-old surfer was reportedly bitten by a shark at "
        "Glenfield Beach, north of Geraldton, Western Australia. Reports describe a "
        "catastrophic right lower-leg injury, rescue by another surfer and beachgoers, "
        "use of a surfboard leg rope as an improvised tourniquet, and serious but stable "
        "hospital condition. Species was not publicly confirmed."
    ),
    "analyst_notes_private": (
        "First real-world AI1SAD incident registry seed case. Keep species unresolved "
        "until official fisheries/DPIRD testing or another documented source supports "
        "a specific identification."
    ),
    "provenance_notes": [
        "ABC reported fisheries/DPIRD testing of the damaged surfboard remained underway as of 2026-09-15.",
        "ABC reported on 2026-09-18 that DNA from the damaged board and wetsuit was still being analysed to determine the most likely species.",
        "Local reporting described the victim as surfing alone before another surfer assisted and the victim was brought to shore.",
        "Media reports describe a surfboard leg rope or ripcord used as an improvised tourniquet by responders at the beach.",
        "Approximate offshore distance and time are retained as reported values, not normalized telemetry.",
    ],
    "normalization_warnings": [
        "species_unconfirmed_public_records",
        "behavior_unknown_insufficient_evidence",
        "coordinates_not_normalized_named_beach_only",
        "injury_details_from_media_reports",
        "active_named_victim_public_citation_metadata_suppressed",
    ],
}


REAL_WORLD_REGISTRY_CASE_PAYLOADS: tuple[dict[str, Any], ...] = (
    GLENFIELD_BEACH_MEL_ISMAIL_2026,
)


def real_world_registry_case_payloads() -> list[dict[str, Any]]:
    """Return deep copies of source-linked real-world registry case payloads."""

    return [deepcopy(payload) for payload in REAL_WORLD_REGISTRY_CASE_PAYLOADS]


def real_world_registry_records(now: datetime | None = None) -> list[IncidentRegistryRecord]:
    """Materialize real-world registry seed cases under the Phase 26B schema."""

    return [
        create_registry_record(payload, now=now)
        for payload in real_world_registry_case_payloads()
    ]
