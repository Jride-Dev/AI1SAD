# Next Phase

## Phase 26C: Australian Archival Newspaper Source Tracker

## Objective

Implement a local/manual metadata-first tracker for Australian archival newspaper and public-record sources that can link into the Phase 26B AI1SAD Shark-Human Incident Registry.

Target full working-version launch: September 7, 2026.

AI1SAD is targeting a full working-version launch on September 7, 2026. Current development is focused on evidence provenance, staged upstream data review, replay explainability, UAV operator workflows, and public-safe surveillance outputs.

Do not start this phase automatically. Phase 26C begins only after Phase 26B is reviewed.

## Current Baseline

Phase 26B leaves AI1SAD with:

- `app/services/incident_registry.py`
- `tests/test_incident_registry.py`
- `docs/SHARK_HUMAN_INCIDENT_REGISTRY.md`
- internal registry record fields for reviewed AI1SAD case records
- source-link support for GSAF rows, future archival newspaper metadata, future Vic Hislop corpus claims, and other evidence lanes
- species and shark-size claim structures
- official/public species status fields separate from internal species hypotheses
- species-disclosure risk guardrails that suppress speculative public species attribution when risk is moderate or high
- behavioral hypothesis support with no default mistaken identity and no confirmed shark-intent claims
- source conflict tracking for species, species disclosure, date, location, fatality, injury, behavioral interpretation, and source reliability disagreements
- public-safe output helpers that exclude private analyst notes, source private notes, internal species hypotheses unless explicitly public-safe and risk-cleared, speculative species guesses, full copyrighted article text, full private quotes, private contact/source details, and uncleared conflict notes
- explicit no-side-effect behavior for warnings, alerts, public feeds, replay facts, scoring, and drone observations

Phase 26B does not add public registry endpoints, public ingestion endpoints, database persistence, Trove scraping, Trove API calls, copyrighted article downloads, replay artifact regeneration, scoring changes, provider adapters, frontend dependencies, or Phase 26C source-capture workflows.

## Planned Scope

1. Define a local/manual archival source metadata model.
2. Capture Trove/National Library of Australia and state-library metadata as citations, not article-body dumps.
3. Preserve OCR uncertainty, source title/date/page fields, source confidence, and rights notes.
4. Support source links into `ai1sad_case_id` registry records without promoting source claims automatically.
5. Track duplicate publications, reprints, syndication, later retellings, and conflicting article claims.
6. Preserve public/private boundaries for excerpts, copyrighted text, private notes, analyst review fields, and species hypotheses.
7. Keep archival source capture separate from warning, alert, replay, scoring, public feed, and drone systems.

## Planned Follow-On Phase

- Phase 26D: Vic Hislop Corpus and Case-Claim Archive
  - Local/manual metadata and claim tracking for Hislop books, interviews, media profiles, Shark Show-era records, shark capture records, and disputed case claims.
  - Claims require corroboration, conflict tracking, controversy flags, and confidence scoring; Hislop sources are not automatically authoritative.

## Likely Files

- `app/services/archival_news_tracker.py`
- `tests/test_archival_news_tracker.py`
- `docs/AUSTRALIAN_ARCHIVAL_NEWS_TRACKER.md`
- `docs/SHARK_HUMAN_INCIDENT_REGISTRY.md`
- `docs/CURRENT_DATA_SOURCES.md`
- `docs/PROJECT_STATUS.md`
- `docs/NEXT_PHASE.md`
- `mkdocs.yml`

## Safety Boundaries

- Do not scrape Trove or other archive pages.
- Do not use the Trove API before terms, quotas, and rights rules are reviewed.
- Do not bulk-download article bodies.
- Do not reproduce copyrighted article text in public outputs.
- Do not create warnings or public alerts from archival records.
- Do not alter scoring weights.
- Do not modify replay outputs or regenerate replay artifacts.
- Do not create public feed entries.
- Do not create drone observations.
- Do not infer shark intent as confirmed behavior.
- Do not default to mistaken identity.
- Do not treat a single archival source as definitive without review.
- Do not promote archival species mentions into public official species confirmation without a reviewed public official source.
- Do not publish speculative species attribution when disclosure risk is moderate or high.

## Validation Expectations

- focused archival tracker tests
- focused incident registry tests if source-link contracts are touched
- full backend tests
- mkdocs build
- README local links/images check
- secret scan
- prohibited-language scan
- git diff --check

## Review Gate

Stop before committing unless explicitly asked to commit Phase 26C work.
