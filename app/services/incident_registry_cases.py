"""Source-linked AI1SAD shark-human incident registry seed cases."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from app.services.incident_registry import IncidentRegistryRecord, create_registry_record


GLENFIELD_BEACH_MEL_ISMAIL_2026_CASE_ID = "AI1SAD-WA-GLENFIELD-BEACH-2026-09-14"
ORIENT_BEACH_SOUTH_AFRICA_2026_CASE_ID = "AI1SAD-ZA-ORIENT-BEACH-2026-10-20"


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


ORIENT_BEACH_SOUTH_AFRICA_2026: dict[str, Any] = {
    "ai1sad_case_id": ORIENT_BEACH_SOUTH_AFRICA_2026_CASE_ID,
    "source_case_ids": [
        "reuters:2026-10-20:orient-beach-fatality",
        "ap:2026-10-20:orient-beach-fatality",
        "timeslive:2026-10-20:orient-beach-fatality",
        "openstreetmap:way:48959821",
    ],
    "registry_version": "AI1SAD-incident-registry-v1",
    "review_status": "source_review",
    "public_visibility": "public",
    "incident_date_raw": "Tuesday 20 October 2026",
    "incident_date_normalized": "2026-10-20",
    "incident_time_raw": "early morning; police attended at about 07:00 local time",
    "timezone": "Africa/Johannesburg",
    "country": "South Africa",
    "region": "Eastern Cape",
    "area": "Buffalo City Metropolitan Municipality / KuGompo City (East London)",
    "location": "Orient Beach",
    "latitude": -33.02495,
    "longitude": 27.91513,
    "coordinate_confidence": "reviewed_named_beach_centroid",
    "water_body": "Indian Ocean",
    "activity": "open-water swimming",
    "victim_context": "65-year-old woman and regular open-water swimmer",
    "human_group_context": (
        "The swimmer was in the water near an open-water swimming group. Fellow swimmers "
        "responded to her distress signal, brought her ashore, and attempted emergency care."
    ),
    "injury_summary": (
        "Fatal injuries after two severe bites reported to the thigh and upper arm; "
        "the swimmer was declared dead at the scene."
    ),
    "injury_severity": "fatal",
    "fatality": True,
    "body_recovered": True,
    "consumption_evidence": "none_reported",
    "official_species_status": "unconfirmed",
    "official_species_name": None,
    "official_species_source_id": None,
    "official_species_public_note": (
        "The shark species was not identified in the reviewed police, municipal, or media reporting."
    ),
    "species_claims": [
        {
            "species_raw": "Unknown shark species",
            "normalized_species": None,
            "source_ids": [
                "reuters:2026-10-20:orient-beach-fatality",
                "ap:2026-10-20:orient-beach-fatality",
            ],
            "confidence": "unknown",
            "attribution_notes": "Reviewed reporting explicitly left the shark species unknown.",
        }
    ],
    "internal_species_hypotheses": [],
    "species_disclosure_risk": "moderate",
    "shark_size_claims": [],
    "behavioral_hypotheses": [
        {
            "hypothesis": "unknown_insufficient_evidence",
            "confidence": "unknown",
            "source_ids": [
                "reuters:2026-10-20:orient-beach-fatality",
                "ap:2026-10-20:orient-beach-fatality",
                "timeslive:2026-10-20:orient-beach-fatality",
            ],
            "rationale": (
                "The reviewed reporting establishes a fatal shark incident but does not "
                "establish shark intent, event mechanics, or a behavioral classification."
            ),
        }
    ],
    "primary_behavioral_hypothesis": "unknown_insufficient_evidence",
    "behavioral_confidence": "unknown",
    "alternative_hypotheses": [],
    "rejected_hypotheses": ["confirmed_shark_intent", "mistaken_identity_candidate"],
    "source_conflicts": [],
    "source_links": [
        {
            "source_id": "reuters:2026-10-20:orient-beach-fatality",
            "source_type": "media_report",
            "source_name": "Reuters",
            "source_url": "https://www.reuters.com/world/africa/woman-dies-after-shark-attack-south-africa-sabc-reports-2026-10-20/",
            "source_date": "2026-10-20",
            "source_title": "Shark kills woman swimming off South Africa's Eastern Cape",
            "source_rights_note": "Citation and paraphrase only; copyrighted article body is not redistributed.",
            "source_confidence": "plausible",
            "linked_claims": [
                "age",
                "date",
                "location",
                "activity",
                "injuries",
                "fatality",
                "rescue_sequence",
                "species_unconfirmed",
                "beach_closures",
            ],
            "public_citation_allowed": True,
        },
        {
            "source_id": "ap:2026-10-20:orient-beach-fatality",
            "source_type": "media_report",
            "source_name": "Associated Press",
            "source_url": "https://apnews.com/article/7b9110691f71319e3c0ecc56ef0567a0",
            "source_date": "2026-10-20",
            "source_title": "Shark kills woman swimming off South Africa's Eastern Cape, beaches closed",
            "source_rights_note": "Citation and paraphrase only; copyrighted article body is not redistributed.",
            "source_confidence": "plausible",
            "linked_claims": [
                "age",
                "date",
                "police_attendance_time",
                "location",
                "activity",
                "fatality",
                "rescue_sequence",
                "inquest",
                "beach_closures",
            ],
            "public_citation_allowed": True,
        },
        {
            "source_id": "timeslive:2026-10-20:orient-beach-fatality",
            "source_type": "media_report",
            "source_name": "TimesLIVE",
            "source_url": "https://www.timeslive.co.za/news/south-africa/2026-10-20-kugompo-city-records-first-fatal-shark-attack-since-1997/",
            "source_date": "2026-10-20",
            "source_title": "KuGompo City records first fatal shark attack since 1997",
            "source_rights_note": "Citation and paraphrase only; copyrighted article body is not redistributed.",
            "source_confidence": "plausible",
            "linked_claims": [
                "age",
                "date",
                "location",
                "fatality",
                "inquest",
                "municipal_history",
                "beach_closures",
            ],
            "public_citation_allowed": True,
        },
        {
            "source_id": "openstreetmap:way:48959821",
            "source_type": "unknown",
            "source_name": "OpenStreetMap",
            "source_url": "https://www.openstreetmap.org/way/48959821",
            "source_title": "Orient Beach mapped feature",
            "source_rights_note": "Named-beach centroid used for public map placement; not an incident-evidence source.",
            "source_confidence": "plausible",
            "linked_claims": ["named_beach_coordinates"],
            "public_citation_allowed": True,
        },
    ],
    "public_summary": (
        "On 2026-10-20, a 65-year-old open-water swimmer died after a shark incident "
        "at Orient Beach in KuGompo City (East London), Eastern Cape, South Africa. "
        "Fellow swimmers brought her ashore and attempted emergency care. The shark "
        "species and behavioral interpretation remain unconfirmed."
    ),
    "analyst_notes_private": (
        "Current-event registry case. Do not infer species, provocation, or shark intent. "
        "Re-review police or municipal findings if the inquest publishes new evidence."
    ),
    "provenance_notes": [
        "Reuters and AP attributed the fatal incident confirmation to Buffalo City municipal authorities.",
        "AP attributed the approximately 07:00 police attendance time and inquest status to Eastern Cape police.",
        "Reuters reported two severe bites based on a witness account; this is retained as attributed reporting, not forensic reconstruction.",
        "The Orient Beach map point is the reviewed named-beach centroid, not a claimed bite coordinate.",
    ],
    "normalization_warnings": [
        "species_unconfirmed_public_records",
        "behavior_unknown_insufficient_evidence",
        "provocation_unclassified",
        "injury_details_from_media_witness_reporting",
        "coordinates_are_named_beach_centroid_not_incident_point",
    ],
}


REAL_WORLD_REGISTRY_CASE_PAYLOADS: tuple[dict[str, Any], ...] = (
    GLENFIELD_BEACH_MEL_ISMAIL_2026,
    ORIENT_BEACH_SOUTH_AFRICA_2026,
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
