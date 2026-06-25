# Vic Hislop Corpus And Case-Claim Archive

This planning page defines a future source lane for Vic Hislop writings, interviews, media appearances, Shark Show-era records, and shark-attack case claims. It supports the planned AI1SAD Shark-Human Incident Registry by preserving provenance, source confidence, controversy, corroboration, and conflicting claims.

This is planning documentation only. Phase 26D has not started.

Target full working-version launch remains September 7, 2026.

## Confidence Model

Vic Hislop sources are treated as historically important, behaviorally relevant, and potentially high-value, but not automatically authoritative. Claims require corroboration, conflict tracking, and confidence scoring.

AI1SAD does not default to mistaken identity. It treats mistaken identity as one possible hypothesis among competing behavioral explanations.

## Source Targets

Initial source targets include:

- `Vic Hislop Shark Man`, 1993
- National Library of Australia catalogue record for `Vic Hislop Shark Man`
- Google Books metadata for `Vic Hislop Shark Man`
- ABC and other media reports about the Hervey Bay Shark Show
- old newspaper articles quoting or profiling Hislop
- interviews
- television/radio appearances
- magazine profiles
- Shark Show museum display claims if sourced by photos/videos/visitor records
- shark capture records attributed to Hislop
- case claims made by Hislop about fatal attacks, missing persons, shark behavior, stomach contents, government records, or disputed explanations

## Planned Fields

The first implementation should capture claim metadata and review state:

- `hislop_source_id`
- `source_type`
- `title`
- `author_or_speaker`
- `publication_or_event_date`
- `publisher_or_platform`
- `url_or_catalogue_ref`
- `archive_location`
- `source_rights_note`
- `claim_type`
- `case_reference_raw`
- `linked_ai1sad_case_id`
- `species_claimed`
- `shark_size_claimed`
- `location_claimed`
- `date_claimed`
- `behavioral_claim`
- `evidence_cited_by_hislop`
- `quote_excerpt_allowed`
- `full_quote_private_only`
- `corroborating_sources`
- `conflicting_sources`
- `claim_confidence`
- `controversy_flag`
- `review_status`
- `analyst_notes_private`

## Supported Source Types

- `authored_book`
- `interview`
- `newspaper_quote`
- `magazine_profile`
- `television_or_radio`
- `museum_display_claim`
- `clipping_reference`
- `case_claim`
- `shark_capture_record`
- `third_party_profile`
- `disputed_claim`

## Supported Claim Types

- `fatal_attack_interpretation`
- `nonfatal_attack_interpretation`
- `missing_person_shark_claim`
- `shark_capture_record`
- `stomach_contents_claim`
- `shark_behavior_claim`
- `government_coverup_claim`
- `conservation_policy_claim`
- `museum_display_claim`
- `personal_experience`
- `disputed_or_uncorroborated`

## Claim Confidence Values

- `unreviewed`
- `unsupported`
- `weak`
- `plausible`
- `corroborated`
- `disputed`
- `contradicted`

## Capture Rules

- Store metadata, citation, claim type, and rights status before any quotation.
- Keep full quotes private unless rights allow public release.
- Use short excerpts only when `quote_excerpt_allowed` is true.
- Preserve the source wording of claims in private review fields where rights allow.
- Track corroborating and conflicting sources separately.
- Mark disputed, controversial, or unsupported claims explicitly.
- Do not treat any Hislop claim as automatically definitive.
- Do not create warnings, alerts, replay facts, scoring changes, public feed entries, or drone observations.
- Do not infer confirmed shark intent from Hislop sources alone.

## Behavioral Hypothesis Link

Vic Hislop sources may inform future AI1SAD behavioral hypotheses:

- `attempted_predation_event`
- `predatory_probe`
- `territorial_displacement`
- `competitive_food_response`
- `scavenging_context`
- `accidental_contact`
- `mistaken_identity_candidate`
- `unknown_insufficient_evidence`

They must support analyst review rather than automatic intent assignment. Claims about predation, repeated engagement, stomach contents, missing persons, scavenging, fishing/bait context, or government records should remain reviewable source claims until corroborated.

## Rights And Public Output

The archive should preserve catalogue references, citations, dates, source type, and claim metadata. Public outputs should avoid full copyrighted passages, unreviewed private notes, and unsupported case narratives.

## Phase 26D Handoff

Phase 26D can implement a local/manual Vic Hislop corpus and case-claim archive after Phase 26B defines the incident registry schema and Phase 26C establishes archival source-tracker patterns. Phase 26D should not start until explicitly approved.
