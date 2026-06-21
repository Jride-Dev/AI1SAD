# Project Status

## Current Snapshot

- Current phase number: Phase 25F (UAV Operator Feedback Intake and Field Requirements Tracker) - implemented locally, uncommitted
- Latest completed committed phase: Phase 25E UAV Operator Research Brief and Compatibility Matrix
- Latest local maintenance: targeted Vite security patch from `7.3.3` to `7.3.5`; frontend/docs/security checks passed, backend suite currently has one unrelated biological-events replay test failure
- Latest commit hash: `e8f85f0` Add UAV operator research brief and compatibility matrix
- Repo status: uncommitted Phase 25F UAV operator feedback intake; verify with `git status`

## Major Completed Systems

- Replay framework and replay library endpoints
- Explainability engine and confidence decomposition
- Regional packs and pack-aware response annotation
- Static/offline providers:
  - Open-Meteo/NOAA wiring support
  - Biological events
  - Vessel and fishing context
  - Human exposure
  - Kelp forest habitat context
  - Hawaii benthic habitat baseline context
  - Hawaii tide/current baseline context
  - Hawaii water clarity/turbidity baseline context
- Frontend trust hardening (fail-closed live mode, explicit mock mode)
- Brand identity integration and docs portal branding
- One-click local launcher scripts
- Phase 25A vendor-neutral drone observation intake MVP in local review: mission records, telemetry ingestion, observation ingestion, map-ready feed, replay fixture support
- Phase 25B read-only MAVLink telemetry bridge committed: JSONL fixture replay, telemetry normalization, bounded batch submission, no aircraft control
- Phase 25C Drone Operator Console implemented locally: `/drone-console`, mission selector, human-entered observation form, recent feed panel, no-sighting patrol copy, and provisional species copy
- Phase 25D-A metadata-only analyst review fields implemented locally: PATCH endpoint for review updates, `analyst_review_status`, `review_outcome`, `public_review_summary`, `analyst_notes_private`, `evidence_confidence`, `media_reference_type`, `media_timestamp` enums, frontend Analyst Review Panel in drone console
- Phase 25D-B media attachment storage design and privacy review: attachment model proposal, storage backend tradeoffs, privacy visibility levels, public-feed rules, security checklist, and implementation gates documented. No storage code added.
- Post-Phase 25D hardening patch committed: raw media references excluded from public drone observation output, impossible confidence values rejected server-side, manual mission selection prefill fixed, and Observation Analyst Review mojibake cleaned up.
- Phase 25D-C local-only media attachment prototype implemented locally: metadata-only attachment records, `MEDIA_ATTACHMENTS_ENABLED=false` default gate, local private filesystem backend label, private-by-default frontend panel, and public-feed privacy filtering. No binary upload, media hosting, computer vision, scoring change, replay change, or autonomous flight behavior added.
- Phase 25D-D media attachment hardening implemented locally: stricter attachment metadata validation for path traversal, absolute paths, Windows drive-root paths, parent-directory references, executable/script filename extensions, unsupported enums, invalid checksums, impossible file sizes, malformed timestamps, and overlong summaries. No binary upload, cloud storage, external fetch, media analysis, scoring change, replay change, or flight-control behavior added.
- Phase 25E UAV operator research brief and compatibility matrix: operator-facing documentation covering manual consumer drone workflow, MAVLink read-only telemetry workflow, post-flight evidence workflow, agency/helicopter report workflow, compatibility matrix, operator questions, minimum field checklist, safety boundaries, and research questions for real UAV operators. Documentation-only phase; no code changes.
- Phase 25F UAV operator feedback intake implemented locally: research-only feedback records, `/api/v1/uav/operator-feedback` POST/GET/PATCH endpoints, frontend `/uav-feedback` submission page, public/private field filtering, enum and length validation, unsafe contact-reference rejection, public-summary contact leakage checks, secret-like text rejection, and no side effects on observations, sightings, warnings, public alerts, replay facts, surveillance feeds, scoring, drone operations, vendor SDKs, media upload, cloud storage, computer vision, or MAVLink command behavior.
- GitHub wiki initialized and structured separately from the main application repo

## Active Safety Rules

- Do not frame outputs as attack probability
- Do not infer shark intent
- Do not tune weights to a single case
- Keep historic/static layers labeled baseline-only
- Do not fabricate unavailable signals
- Preserve strict timeline separation for replay case studies

## Current Known Gaps

- Tide-state adapter has static/offline baseline support; live ingestion not yet integrated
- Current-direction/speed adapter has static/offline baseline support; live ingestion not yet integrated
- Water clarity/turbidity adapter has static/offline baseline support; live ingestion not yet integrated
- Live surf-line/lifeguard observation ingestion is supported through the local console/API path when drone ingestion is enabled; broader provider-style ingestion remains future work
- Live sightings ingestion pipeline still limited
- Drone intake is vendor-neutral observation ingestion only; it does not provide aircraft control, image hosting, or computer-vision inference.
- Drone Operator Console media references are references only; image upload, media hosting remain future work (design documented in Phase 25D-B).
- Raw drone media references are private-by-default and excluded from public responses until future public-safe release rules exist.
- Analyst review fields are metadata-only annotations; AI1SAD does not fetch, host, or analyze media.
- Local media attachments are metadata-only and disabled by default; binary upload, public attachment release, authentication, malware scanning, EXIF/geotag stripping, and production upload hardening remain future work.
- MAVLink bridge is read-only telemetry-only; `.tlog` parsing and UDP live parsing remain future/reviewed work.
- UAV operator feedback is research/requirements input only; Phase 25G still needs a review dashboard and requirements prioritization workflow.
- Hawaii cohort expansion (10-20 strict timeline-separated cases) not yet complete
- WA carcass replay exposes the need for tide/current drift support before down-current corridor recommendations can become data-backed
- Greater Recife replay exposes missing Pernambuco regional-pack, reef-barrier, tide/current, turbidity, human-exposure, and monitoring-program ingestion support
- Michaelmas Island replay shows high WA spearfishing/offshore surveillance context even before post-incident signals, with missing live weather/ocean/sighting sources.
- Lovers Point replay shows carcass and closure surveillance context while drift direction remains unavailable until tide/current fixture support exists.
- Coogee Beach Sydney 2026 replay keeps strict pre-incident and quiet-day runs low, then documents post-incident closure, drone/helicopter aerial footage evidence, rescuer account, and aviation-restricted drone-review context without adding providers or invented live conditions. Probable white shark remains preliminary/source-attributed; same-individual link is unconfirmed. Possible blood plume is analyst visual assessment uncertainty.

## Next Planned Phase

- Phase 25G: UAV Feedback Review Dashboard and Requirements Prioritization
- Planning details: see [NEXT_PHASE.md](NEXT_PHASE.md)

## Local Startup Instructions

From repo root:

- Double-click `start_ai1sad_demo.bat`, or run:
  - `start_ai1sad_demo.ps1`

Manual fallback:

- Backend:
  - `python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - Windows fallback: `F:\Python310\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend:
  - `cd frontend`
  - `npm run dev -- --host 0.0.0.0 --port 5174`
- MkDocs:
  - `mkdocs serve --dev-addr 0.0.0.0:8001`

Stop scripts:

- `stop_ai1sad_demo.bat`
- `stop_ai1sad_demo.ps1`

## Local URLs

- Frontend: [http://localhost:5174](http://localhost:5174)
- FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- MkDocs: [http://localhost:8001](http://localhost:8001)

Note: FretTrack may occupy `5173`; AI1SAD runs on `5174`.

## Validation Counts (Latest Completed Commit)

- Phase 25B focused MAVLink bridge tests: `11 passed`
- Phase 25B focused drone-ingestion tests: `10 passed, 1 warning`
- Phase 25B focused Panama City replay tests: `3 passed`
- Phase 25B full backend tests: `253 passed, 3 warnings`
- Phase 25B MkDocs build: passed with the standard Material for MkDocs advisory banner
- Phase 25B secret scan on changed files: no credential values; variable/config names only for `AI1SAD_DRONE_API_KEY`
- Phase 25B prohibited-language scan: guardrail-only matches in docs

## Validation Counts (Latest Coogee Local Run)

- Focused replay tests: `45 passed`
- Replay-library tests: `4 passed, 3 warnings`
- Full backend tests: `255 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- JSON/SVG parse checks: passed for Coogee replay, factor summary, and heatmap artifacts
- Secret scan on changed files: no matches
- Prohibited-language scan on changed files: guardrail/test-only matches only
- Local environment note: `pydantic-core` was corrected to `2.46.4` to match installed `pydantic 2.13.4` before backend validation

## Validation Counts (Latest Dependency Security Maintenance)

- GitHub Dependabot open alerts reviewed: `2` Vite alerts (`1 high`, `1 medium`)
- Patched package: `vite 7.3.3` -> `7.3.5`
- Separate `launch-editor` fix required: no; `npm ls launch-editor` is empty after the Vite patch
- Frontend tests: `5` files passed, `30` tests passed
- Frontend build: passed with Vite `7.3.5`
- Frontend audit high: `0` high or critical vulnerabilities; one low `@babel/core` advisory remains outside the Vite-alert scope
- Backend tests:
  - `python -m pytest -q` with system Python 3.14 failed during collection because `pymongo` was not installed in that interpreter
  - `F:\Python310\python.exe -m pytest -q` ran with `282 passed, 1 failed, 3 warnings`
  - Failing test: `tests/test_biological_events_provider.py::test_lovers_point_carcass_warning_is_bounded`
  - Failure was not patched because it is unrelated to the Vite dependency update and would require provider/replay/scoring work outside this maintenance scope
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local link/image check: `54` checked, passed
- Secret scan on changed files: no credential matches
- Prohibited-language scan on changed files: no matches
- Git whitespace check: passed with CRLF normalization warnings only
- GitHub Dependabot API before commit/push: still reported alerts #5 and #6 open on the remote default branch; recheck after the patch is pushed

## Validation Counts (Previous Dependency Security Maintenance)

- GitHub Dependabot open alerts reviewed: `2` esbuild alerts (`1 high`, `1 low`)
- Patched package: `esbuild 0.27.7` -> `0.28.1` through a targeted frontend npm override
- Frontend tests: `3 passed`, `8 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend audit: `npm audit --audit-level=high` reported `0 vulnerabilities`
- Backend tests: `255 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- Secret scan on changed files: no credential values; documentation phrases and `js-tokens` package names only
- Prohibited-language scan on changed files: guardrail-only matches only

## Validation Counts (Post-Phase 25D Hardening Local Run)

- Focused drone observation ingestion tests: `23 passed, 1 warning`
- Full backend tests: `268 passed, 3 warnings`
- Frontend tests: `22 passed`
- Frontend build: passed
- Frontend npm audit high: `0 vulnerabilities`
- MkDocs build: passed
- Secret scan: no credential matches
- Prohibited-language scan: guardrail/disclaimer matches only
- Public output hardening: `media_reference`, `media_reference_type`, and `media_timestamp` excluded via `PUBLIC_DROP_FIELDS`
- Confidence validation: invalid `confidence` and `evidence_confidence` values now return 422; valid `0` and `1` boundaries accepted
- Frontend hardening: Analyst Review cards no longer render raw media references; manual mission fetch selects using fetched mission detail instead of stale state

## Validation Counts (Latest Phase 25D-C Local Run)

- Focused drone observation ingestion tests: `29 passed, 1 warning`
- Full backend tests: `274 passed, 3 warnings`
- Frontend tests: `4 files passed`, `25 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend npm audit high: `0 vulnerabilities`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local link/image check: `49` links/images checked; local targets exist
- Secret scan: no credential matches
- Prohibited-language scan: guardrail/disclaimer matches only
- Git whitespace check: passed with CRLF normalization warnings only
- Current implementation: metadata-only local attachment records, disabled by default behind `MEDIA_ATTACHMENTS_ENABLED`, no binary upload, no external media fetching, no computer vision, no public feed exposure, and no scoring/replay changes

## Validation Counts (Latest Phase 25D-D Local Run)

- Focused drone observation ingestion tests: `30 passed, 1 warning`
- Full backend tests: `275 passed, 3 warnings`
- Frontend tests: `4 files passed`, `26 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend npm audit high: `0 vulnerabilities`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local link/image check: `49` links/images checked; local targets exist
- Secret scan: no credential matches
- Prohibited-language scan: guardrail/disclaimer matches only
- Git whitespace check: passed with CRLF normalization warnings only
- Current implementation: hardened metadata validation only; no binary upload, cloud storage, external media fetching, computer vision, media-based species inference, sighting creation, public media exposure, scoring change, or replay change

## Validation Counts (Latest Phase 25D-A Local Run)

- Backend: PATCH endpoint for analyst review update, enum validation, private field filtering
- Frontend: AnalystReviewPanel component, submitObservationReview API client, mock data fixtures
- Analyst review fields: media_reference_type, analyst_review_status, review_outcome, evidence_confidence, analyst_notes_private (filtered from public output), public_review_summary
- enum validation: unsupported media_reference_type, analyst_review_status, review_outcome rejected with 422
- PATCH endpoint validates enum values server-side and rejects unsupported types
- `analyst_notes_private`, `analyst_reviewer_role`, `analyst_reviewed_at` excluded via PUBLIC_DROP_FIELDS
- Frontend private notes warning visible: "Analyst notes remain private and are never returned in public feed output."
- No computer vision, media upload/hosting, or autonomous flight control added

## Validation Counts (Latest Phase 25C Local Run)

- Frontend route added: `http://localhost:5174/drone-console`
- Backend changes: existing drone endpoints reused; `other` accepted as a generic bounded observation type
- Frontend tests: `4 passed`, `17 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend audit: `npm audit --audit-level=high` reported `0 vulnerabilities`
- Focused drone-ingestion tests: `11 passed, 1 warning`
- Focused MAVLink bridge tests: `11 passed`
- Focused Panama City replay tests: `3 passed`
- Full backend tests: `256 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README link/image check: passed after skipping HTML tags/placeholders
- Secret scan on changed docs/code: no credential values; documentation phrases, placeholder config names, and existing test key strings only
- Prohibited-language scan on changed docs/code: required safety-copy and guardrail/test-only matches only

## Validation Counts (Latest Phase 25E Local Run)

- MkDocs build: passed (2.53s, known Material advisory only)
- README local link/image check: 66 checked, passed
- Secret scan: passed
- Prohibited-language scan: passed
- git whitespace check: passed (CRLF warnings only)
- No code changed: backend/frontend tests not required

## Validation Counts (Latest Phase 25F Local Run)

- Focused UAV feedback tests: `8 passed, 1 warning`
- Full backend tests: `283 passed, 3 warnings`
- Frontend tests: `5 files passed`, `30 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend npm audit high: `0 vulnerabilities`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local link/image check: `52` links/images checked; local targets exist
- Secret scan: no credential matches
- Prohibited-language scan: guardrail/disclaimer/test-only matches only
- Git whitespace check: passed with CRLF normalization warnings only
- Current implementation: research-only UAV operator feedback intake, private-by-default contact fields, public-safe output filtering, no observation/sighting/feed creation, no warnings or public alerts, no replay/scoring changes, no drone operations, no SDK integrations, no media upload, no cloud storage, no computer vision, and no MAVLink command behavior.

## Validation Counts (Latest Coogee Media Evidence Update)

- Focused replay tests: pending
- Replay-library tests: pending
- Full backend tests: pending
- MkDocs build: pending
- JSON/SVG parse checks: pending
- Secret scan: pending
- Prohibited-language scan: pending

## Current Review Item

- Phase 25F UAV Operator Feedback Intake and Field Requirements Tracker awaiting review.
- Adds `app/services/uav_operator_feedback.py` for bounded validation, public/private output filtering, and research-only side-effect flags.
- Adds `/api/v1/uav/operator-feedback` POST/GET/PATCH endpoints for feedback submission, listing, and status updates.
- Adds frontend route `http://localhost:5174/uav-feedback` with required safety/privacy copy, feedback submission form, validation errors, backend unavailable state, and success summary.
- Adds `docs/UAV_OPERATOR_FEEDBACK_INTAKE.md` and updates README, API docs, drone docs, current data sources, UAV research docs, MkDocs navigation, and next-phase handoff.
- Feedback remains requirements input only. It does not create observations, sightings, public feed entries, warnings, public alerts, replay facts, scoring changes, drone operations, SDK integrations, media upload, cloud storage, computer vision, or MAVLink command behavior.
- Review gate: do not commit until reviewed; do not begin Phase 25G.

## Recent Important Commits

- `e8f85f0` Add UAV operator research brief and compatibility matrix
- `fe5b230` Harden local media attachment metadata validation
- `1996b0a` Add AI1SAD repository agent instructions
- `bc6c5c9` Add local media attachment metadata prototype
- `5ec0881` Harden drone observation privacy and validation
- `837a8cd` Patch Dependabot security alerts
- `fe63fe0` Add Coogee Beach Sydney replay case study
- `f737cd1` Add read-only MAVLink telemetry bridge
- `53ebbf1` Update README featured replay preview
- `3b1f267` Refresh GitHub README with current AI1SAD status
- `6a9e864` Add NSA Panama City drone-observation replay case study
- `5e38e09` Add vendor-neutral drone observation intake MVP
- `2f9c305` Add Michaelmas Island and Lovers Point replay case studies
- `10d4dd6` Add Hawaii water clarity and turbidity adapter
- `3ece14a` Add paired Recife shark-incident replay case study
- `1fcdf62` Add Greater Recife paired replay case study
- `c50441a` Add Hawaii tide and current context adapter
- `363c359` Patch frontend Vitest security advisory
- `a03cc7b` Add Plumpudding Beach whale-carcass replay case study
- `02b7138` Fix replay sighting evaluation against scenario timestamps
- `ce1373a` Add durable project status and next-phase handoff
- `e880846` Add Hawaii habitat mapping adapter
- `5d5aa79` Add Hawaii signal gap analysis
- `941416c` Add Cromwells Beach Hawaii replay case study
- `9e3d112` Add bounded kelp forest habitat signal layer
- `a9a8542` Harden public API query handling and error metadata
- `3f6ce69` Fix frontend live-data trust and replay selection handling
- `ba6d3df` Integrate AI1SAD brand assets across platform
- `90e540e` Add one-click local demo launcher
- `5b5937a` Phase 25D-A: metadata-only analyst review fields for observations
- `c4f12bd` Clarify consumer drone app compatibility
