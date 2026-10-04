# Next Phase

## Incident Globe Handoff

The local 2000-2026 Incident Globe is implemented before further historical expansion. It contains `3,398` deduplicated records, plots `1,927` validated coordinates, and explicitly retains `1,471` unresolved locations off-map. The mapped total includes `452` source coordinates and `1,475` contextual results validated against relevance, stated-country boundaries, and a 25 km coastline limit. A sanitized 1900-2026 batch and validated cache are preserved for future pre-2000 decade layers; those historical decades are not yet published. The current globe includes decade, Provoked/Unprovoked, and bounded outcome filters with source-attributed click-through infographics.

Future globe work is limited to human-reviewed coordinate resolution, rights-cleared case media, and pre-2000 decade layers. Likely source matches must not be auto-merged, unresolved places must not receive guessed coordinates, and the view must not alter scoring, warnings, alerts, replay outputs, species determinations, or shark-intent interpretation. See [Incident Globe](INCIDENT_GLOBE.md).

The next planned numbered phase remains Phase 26D. Target full working-version launch remains September 7, 2026.

## Deployment Handoff

The frontend, Incident Globe, and email routing are live at `ai1sad.org`. The free Render Docker API, MongoDB Atlas connection, DNS-only `api.ai1sad.org` CNAME, managed TLS, CORS, production API smoke checks, frontend production routing, and live Incident Globe verification are complete. Remaining operational work is to create the Cloudflare Pages documentation project. Target full working-version launch remains September 7, 2026.

## Phase 26D: Vic Hislop Corpus And Case-Claim Archive

## Objective

Implement a local/manual metadata-first corpus and case-claim archive for Vic Hislop writings, interviews, media appearances, Shark Show-era records, shark capture records, and disputed case claims that can link into the AI1SAD Shark-Human Incident Registry.

Target full working-version launch: September 7, 2026.

AI1SAD is targeting a full working-version launch on September 7, 2026. Current development is focused on evidence provenance, staged upstream data review, replay explainability, UAV operator workflows, and public-safe surveillance outputs.

Do not start this phase automatically. Phase 26D begins only after Phase 26C is reviewed.

## Current Baseline

Phase 26C leaves AI1SAD with:

- `app/services/incident_registry.py`
- `app/services/incident_registry_cases.py`
- `app/services/archival_news_tracker.py`
- `tests/test_incident_registry.py`
- `tests/test_archival_news_tracker.py`
- `docs/SHARK_HUMAN_INCIDENT_REGISTRY.md`
- `docs/AUSTRALIAN_ARCHIVAL_NEWS_TRACKER.md`
- internal registry record fields for reviewed AI1SAD case records
- source-link support for GSAF rows, archival newspaper metadata, Trove metadata, state-library records, government reports, coroner/inquest references, future Vic Hislop corpus claims, and other evidence lanes
- local/manual archival source metadata records for citations, rights state, OCR uncertainty, duplicate/reprint context, source conflicts, source confidence, and registry source-link conversion
- JSON/CSV CLI import for manually prepared archival metadata files into ignored local staging/report JSON under `data/imports/archival_news/`
- Windows `.bat`/`.exe` launchers for local archival imports with optional Mongo credential prompting
- opt-in internal MongoDB persistence for accepted archival metadata records and sanitized import reports
- public-safe archival output that excludes private notes, named people, raw OCR dumps, full article text, downloaded HTML, and unauthorized excerpts
- article-body/raw-OCR rejection and blocked scraping/API/bulk-download capture modes
- species and shark-size claim structures
- official/public species status fields separate from internal species hypotheses
- species-disclosure risk guardrails that suppress speculative public species attribution when risk is moderate or high
- behavioral hypothesis support with no default mistaken identity and no confirmed shark-intent claims
- source conflict tracking for species, species disclosure, date, location, fatality, injury, behavioral interpretation, rights, and source reliability disagreements
- public-safe output helpers that exclude private analyst notes, source private notes, internal species hypotheses unless explicitly public-safe and risk-cleared, speculative species guesses, full copyrighted article text, full private quotes, private contact/source details, and uncleared conflict notes
- explicit no-side-effect behavior for warnings, alerts, public feeds, replay facts, scoring, drone observations, provider adapters, Trove API use, scraping, article downloads, and frontend dependencies
- an independent private Sharks Happen workbook source lane with `864` attributed source records, registry-compatible source links, Mongo persistence, and a human-review duplicate queue against the existing normalized source database

The Sharks Happen intake is a bounded source addition and does not begin Phase 26D. Its `162` exact and `435` likely cross-source candidates remain unmerged; `267` rows are unmatched, not rejected.

Phase 26C does not add public registry endpoints, public archival endpoints, public ingestion endpoints, Trove scraping, Trove API calls, copyrighted article downloads, raw OCR storage, replay artifact regeneration, scoring changes, provider adapters, frontend dependencies, alerts, public-feed observations, drone observations, or Phase 26D Hislop workflows. Its database use is limited to opt-in internal archival metadata/report persistence from the local CLI.

## Planned Scope

1. Define a local/manual Hislop source and case-claim metadata model.
2. Capture book, interview, catalogue, media, Shark Show, shark capture, and disputed case-claim metadata as citations, not full copyrighted text dumps.
3. Preserve source title/date/platform, source confidence, rights notes, controversy flags, corroborating sources, conflicting sources, and review state.
4. Support source links into `ai1sad_case_id` registry records without promoting Hislop claims automatically.
5. Track claim types such as fatal-attack interpretation, missing-person shark claims, shark capture records, stomach-content claims, shark-behavior claims, government-record claims, museum-display claims, and disputed or uncorroborated claims.
6. Preserve public/private boundaries for excerpts, copyrighted text, private notes, analyst review fields, species hypotheses, and retaliation-sensitive details.
7. Keep Hislop claim capture separate from warning, alert, replay, scoring, public feed, provider, and drone systems.

## Likely Files

- `app/services/vic_hislop_archive.py`
- `tests/test_vic_hislop_archive.py`
- `docs/VIC_HISLOP_CORPUS_ARCHIVE.md`
- `docs/SHARK_HUMAN_INCIDENT_REGISTRY.md`
- `docs/CURRENT_DATA_SOURCES.md`
- `docs/PROJECT_STATUS.md`
- `docs/NEXT_PHASE.md`
- `docs/SCHEMA.md`

## Safety Boundaries

- Do not bulk-download copyrighted books, articles, transcripts, or media.
- Do not reproduce copyrighted passages in public outputs.
- Do not treat Hislop claims as automatically authoritative.
- Do not create warnings or public alerts from Hislop records.
- Do not alter scoring weights.
- Do not modify replay outputs or regenerate replay artifacts.
- Do not create public feed entries.
- Do not create drone observations.
- Do not infer shark intent as confirmed behavior.
- Do not default to mistaken identity.
- Do not treat a single Hislop claim as definitive without corroboration.
- Do not promote Hislop species mentions into public official species confirmation without a reviewed public official source.
- Do not publish speculative species attribution when disclosure risk is moderate or high.

## Validation Expectations

- focused Hislop archive tests
- focused incident registry tests if source-link contracts are touched
- focused archival tracker tests if shared patterns are touched
- full backend tests
- mkdocs build
- README local links/images check
- secret scan
- prohibited-language scan
- git diff --check

## Review Gate

Stop before committing unless explicitly asked to commit Phase 26D work.
