# Shark-Human Incident Registry

Phase 26B adds the first internal AI1SAD Shark-Human Incident Registry schema.

Target full working-version launch remains September 7, 2026.

The registry is not a clone of ISAF/GSAF and is not a public incident feed. It is an internal reviewed case-record model that can link multiple upstream evidence lanes while preserving provenance, uncertainty, source conflicts, species-disclosure boundaries, behavioral-hypothesis review, public-safe summaries, and private analyst notes.

## Scope

Phase 26B adds:

- `app/services/incident_registry.py`
- synthetic focused tests in `tests/test_incident_registry.py`
- internal schema/service helpers for registry records, source links, official species status, internal species hypotheses, species-disclosure risk, behavioral hypotheses, source conflicts, and public-safe output

Phase 26B does not add public ingestion endpoints, public registry endpoints, database persistence, warning creation, alert creation, replay changes, scoring changes, drone observations, Trove scraping, Trove API calls, raw GSAF row publication, or copyrighted article downloads.

## Registry Record Purpose

AI1SAD now separates three layers:

- Upstream source rows or citations: GSAF staging rows, archival newspaper metadata, catalogue references, Hislop corpus claims, local authority records, interviews, scientific papers, and other source evidence.
- Internal AI1SAD registry records: reviewed case records with source provenance, confidence, conflict tracking, and public/private fields.
- Public API incidents: scrubbed public records only after future release rules and review gates.

The registry is the middle layer. It can store evidence relationships and uncertainty before any public release or model use.

## Core Fields

The internal model includes:

- `ai1sad_case_id`
- `registry_version`
- `created_at`
- `updated_at`
- `review_status`
- `public_visibility`
- `incident_date_raw`
- `incident_date_normalized`
- `incident_time_raw`
- `country`
- `region`
- `area`
- `location`
- `latitude`
- `longitude`
- `coordinate_confidence`
- `water_body`
- `activity`
- `victim_context`
- `human_group_context`
- `injury_summary`
- `injury_severity`
- `fatality`
- `body_recovered`
- `consumption_evidence`
- `official_species_status`
- `official_species_name`
- `official_species_source_id`
- `official_species_public_note`
- `species_claims`
- `internal_species_hypotheses`
- `species_disclosure_risk`
- `shark_size_claims`
- `source_links`
- `behavioral_hypotheses`
- `primary_behavioral_hypothesis`
- `behavioral_confidence`
- `alternative_hypotheses`
- `rejected_hypotheses`
- `source_conflicts`
- `public_summary`
- `analyst_notes_private`
- `provenance_notes`
- `normalization_warnings`

Precise dates and coordinates should only be normalized when sources support them. Vague dates, approximate locations, OCR uncertainty, and conflicting species claims should remain visible as review metadata.

## Source Link Model

Each registry record can link multiple sources. Source links include:

- `source_id`
- `source_type`
- `source_name`
- `source_ref`
- `source_url`
- `source_date`
- `source_title`
- `source_rights_note`
- `source_confidence`
- `linked_claims`
- `quote_excerpt_allowed`
- `quote_excerpt`
- `public_citation_allowed`
- `full_quote_private_only`
- `full_copyrighted_article_text`
- `private_contact_or_source_details`
- `private_notes`

Supported source types include:

- `gsaf_row`
- `isaf_reference`
- `archival_newspaper`
- `trove_metadata`
- `state_library_record`
- `government_report`
- `coroner_or_inquest`
- `surf_lifesaving_record`
- `vic_hislop_corpus`
- `interview`
- `media_report`
- `scientific_paper`
- `eyewitness_statement`
- `local_authority`
- `unknown`

GSAF links are preserved as upstream source references, not final AI1SAD case truth. Archival newspaper links should preserve OCR/source uncertainty and rights status. Vic Hislop links can inform claims and hypotheses, but are not automatically authoritative.

## Species Disclosure Model

Phase 26B separates public official species status from internal analyst species hypotheses.

Official species status values are:

- `confirmed_public`
- `confirmed_not_publicly_disclosed`
- `unconfirmed`
- `disputed`
- `unknown`
- `not_applicable`

Official fields are:

- `official_species_status`
- `official_species_name`
- `official_species_source_id`
- `official_species_public_note`

If public official sources do not name a species, `official_species_status` must not be `confirmed_public`. A `confirmed_public` value requires both a public official species name and a source id. Internal analyst hypotheses are never promoted into `official_species_name`.

Internal species hypotheses include:

- `species_common_name`
- `species_scientific_name`
- `claim_status`
- `confidence`
- `basis`
- `limitations`
- `source_ids`
- `visibility`
- `analyst_notes_private`

Supported internal claim statuses are `inferred`, `analyst_hypothesis`, `source_claimed`, `official_confirmed_private`, `disputed`, and `rejected`. Supported visibility values are `internal_review_only`, `public_safe`, `restricted`, and `suppressed_for_retaliation_risk`.

`species_disclosure_risk` can be `none`, `low`, `moderate`, `high`, or `unknown`. Species guesses are private by default. Public-safe output suppresses internal species hypotheses unless they are explicitly marked `public_safe`, and it suppresses speculative species attribution whenever disclosure risk is `moderate` or `high`.

Required public-safe uncertainty wording:

> Species was not officially confirmed in public records. AI1SAD preserves the uncertainty and does not publish speculative species attribution where doing so could encourage retaliation or distort the source record.

## Behavioral Hypothesis Model

Supported behavioral hypotheses are:

- `attempted_predation_event`
- `predatory_probe`
- `territorial_displacement`
- `competitive_food_response`
- `scavenging_context`
- `accidental_contact`
- `mistaken_identity_candidate`
- `defensive_response`
- `investigative_contact`
- `object_contact_or_investigative_bite`
- `unknown_insufficient_evidence`

Supported confidence values are:

- `unknown`
- `weak`
- `plausible`
- `probable`
- `corroborated`
- `disputed`
- `contradicted`

Rules:

- AI1SAD does not default to mistaken identity.
- AI1SAD does not claim confirmed shark intent.
- Multiple competing hypotheses are allowed.
- A primary hypothesis requires at least `weak` confidence.
- Questionable, unsupported, unreviewed, or unconfirmed evidence leaves the primary hypothesis as `unknown_insufficient_evidence`.
- GSAF row categories can inform context but do not decide behavior.
- Archival newspaper claims must preserve OCR/source uncertainty.
- Vic Hislop claims require corroboration, conflict tracking, and confidence review.

## Conflict Tracking

The registry can track source conflicts across:

- species disagreement
- date disagreement
- location disagreement
- fatality disagreement
- injury disagreement
- behavioral interpretation disagreement
- source reliability disagreement
- species disclosure disagreement

Conflict fields include:

- `conflict_id`
- `conflict_type`
- `summary`
- `sources_in_conflict`
- `current_resolution`
- `resolution_confidence`
- `public_summary_allowed`
- `analyst_notes_private`

Conflict records are not flattened into a single narrative. Public-safe output includes conflict summaries only when explicitly marked as public-safe.

## Public-Safe Output

`public_safe_registry_output` returns a scrubbed representation for future public-review or release workflows.

Public-safe output excludes:

- `analyst_notes_private`
- source `private_notes`
- internal species hypotheses unless explicitly marked `public_safe`
- speculative species guesses when official species is unconfirmed
- speculative species attribution when species-disclosure risk is `moderate` or `high`
- `full_copyrighted_article_text`
- `full_quote_private_only`
- private contact or source details
- internal conflict notes that are not cleared for public summary
- retaliation-sensitive details

Public-safe output may include:

- `ai1sad_case_id`
- public summary
- general date and location fields
- public-safe citations where `public_citation_allowed` is true
- public-safe quote excerpts where `quote_excerpt_allowed` is true
- official species status
- official species name only when the species is confirmed in public official sources
- the public-safe species uncertainty note
- explicitly public-safe internal species hypotheses only when disclosure risk allows them
- public-safe behavioral hypotheses and confidence
- review status
- safe normalization warnings
- public-approved conflict summaries

## Side-Effect Boundaries

Registry records do not create or modify:

- warnings
- public alerts
- public feed entries
- replay facts or replay artifacts
- scoring weights
- drone observations
- provider adapters
- frontend dependencies

Phase 26B is schema/service foundation only. Promotion workflows, database persistence, API routes, and public release rules remain future work.

## Known Limitations

- The registry is an in-process service/schema foundation, not a persisted database collection.
- No public or internal API route is added in Phase 26B.
- Synthetic tests exercise the schema and public-safe helper; they do not import real GSAF rows, scrape Trove, use the Trove API, or include copyrighted article bodies.
- Species disclosure review still needs future workflow, reviewer roles, storage, and public-release policy before production use.

## Validation Snapshot

Latest Phase 26B local validation:

- Focused incident registry tests: `13 passed`
- Full backend tests: `309 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local links/images check: `58` checked, passed
- Secret scan on changed files: no credential patterns matched
- Prohibited-language scan on changed files: guardrail/disclaimer/test-only matches only
- Git whitespace check: passed with CRLF normalization warnings only

No replay outputs, scoring weights, provider adapters, frontend dependencies, fixture dates, public feeds, alerts, warnings, drone observations, Trove scraping, Trove API calls, or copyrighted article downloads changed.

## Next Phase

The next planned phase is Phase 26C: Australian Archival Newspaper Source Tracker.

Phase 26C should implement local/manual metadata capture for archival sources that can link into this registry. It must not scrape Trove, use the Trove API, bulk-download copyrighted article bodies, or create warning/scoring/replay side effects.
