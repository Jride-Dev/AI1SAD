# Next Phase

## Phase 26B: AI1SAD Shark-Human Incident Registry Schema

## Objective

Design the first-class AI1SAD shark-human incident registry schema that can receive reviewed upstream source records without treating GSAF staging rows as final public incidents.

Target full working-version launch: September 7, 2026.

AI1SAD is targeting a full working-version launch on September 7, 2026. Current development is focused on evidence provenance, staged upstream data review, replay explainability, UAV operator workflows, and public-safe surveillance outputs.

Do not start this phase automatically. Phase 26B begins only after Phase 26A is reviewed.

## Current Baseline

Phase 26A leaves AI1SAD with:

- `app/services/gsaf_importer.py`
- local `python -m app.services.gsaf_importer` entry point
- manual `.csv`, `.xlsx`, and `.xls` GSAF intake
- normalized internal staging JSON
- stable source-field row fingerprints
- baseline delta reporting for new, changed, unchanged, duplicate, malformed, and possibly removed rows
- provenance fields for source file, source row number, source case number, raw dates, raw species, raw source notes, and raw GSAF type
- provisional behavioral hypothesis candidates with confidence labels
- no warnings, alerts, replay facts, public feed entries, drone observations, scoring changes, or raw-row redistribution

Additional planning docs now describe two later source lanes:

- Phase 26C: Australian Archival Newspaper Source Tracker
- Phase 26D: Vic Hislop Corpus and Case-Claim Archive

These planning docs do not start Phase 26B, Phase 26C, or Phase 26D implementation.

A Phase 26A follow-up backend maintenance fix resolves the known Lovers Point biological-event freshness test before Phase 26B. Biological-event freshness can now be evaluated at the replay scenario timestamp for strict replay runs, while default live/API warning behavior still uses current wall-clock time. No scoring weights, fixture dates, replay outputs, providers, frontend dependencies, or dependency-security files changed.

## Planned Scope

1. Define the AI1SAD shark-human incident registry schema.
2. Separate reviewed internal incidents from upstream source staging records.
3. Preserve source provenance, source confidence, source licensing/redistribution status, and review status.
4. Model incident date precision without inventing exact dates from vague sources.
5. Model species assessment provenance and confidence.
6. Model behavioral hypotheses as provisional analyst-reviewed fields, not confirmed intent.
7. Define merge/deduplication rules for multiple upstream sources pointing at one incident.
8. Define privacy/public-release fields before any public output path exists.
9. Keep registry ingestion separate from warning, alert, replay, scoring, and drone systems unless a later reviewed phase explicitly bridges them.

## Planned Follow-On Phases

- Phase 26C: Australian Archival Newspaper Source Tracker
  - Local/manual metadata-first capture for Trove, Australian state libraries, local newspapers, surf lifesaving histories, legal/inquest references where accessible, fisheries/shark-control reports, and maritime accident archives.
  - No scraping, Trove API use, bulk article-body downloads, or public copyrighted-article reproduction without explicit rights review.
- Phase 26D: Vic Hislop Corpus and Case-Claim Archive
  - Local/manual metadata and claim tracking for Hislop books, interviews, media profiles, Shark Show-era records, shark capture records, and disputed case claims.
  - Claims require corroboration, conflict tracking, controversy flags, and confidence scoring; Hislop sources are not automatically authoritative.

## Likely Files

- `app/models.py`
- `app/mongodb.py`
- `app/services/incident_registry.py`
- `tests/test_incident_registry.py`
- `docs/SCHEMA.md`
- `docs/CURRENT_DATA_SOURCES.md`
- `docs/GSAF_IMPORT_AND_DELTA_TRACKING.md`
- `docs/PROJECT_STATUS.md`
- `docs/NEXT_PHASE.md`
- `mkdocs.yml`

## Safety Boundaries

- Do not overwrite existing AI1SAD incident data.
- Do not publish raw GSAF rows.
- Do not create warnings or public alerts from staged or registry records.
- Do not alter scoring weights.
- Do not modify replay outputs.
- Do not create drone observations.
- Do not add scraping or live upstream fetches.
- Do not infer shark intent as confirmed behavior.
- Do not default to mistaken identity.
- Do not claim individual incident probability or safety guarantees.
- Do not bulk-download archival newspaper text or reproduce copyrighted articles.
- Do not treat any single archival source or Vic Hislop claim as definitive without review.

## Validation Expectations

- focused incident-registry tests
- focused GSAF importer tests if registry touches staging contracts
- full backend tests
- mkdocs build
- README local links/images check
- secret scan
- prohibited-language scan
- git diff --check

## Review Gate

Stop before committing unless explicitly asked to commit Phase 26B work.
