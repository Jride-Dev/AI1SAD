# Project Status

## Current Snapshot

- Current phase number: Phase 25B (Read-Only MAVLink Telemetry Bridge)
- Latest completed committed phase: Phase 25A (Drone Observation Intake MVP and NSA Panama City replay)
- Latest completed local phase: Phase 25B in progress, uncommitted (Read-Only MAVLink Telemetry Bridge)
- Latest commit hash before Phase 25B commit: `53ebbf1` Update README featured replay preview
- Repo status: clean before Phase 25B local changes except for any user-created untracked files; verify with `git status`

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
- Phase 25B read-only MAVLink telemetry bridge in local review: JSONL fixture replay, telemetry normalization, bounded batch submission, no aircraft control

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
- Live surf-line/lifeguard observation ingestion not yet integrated
- Live sightings ingestion pipeline still limited
- Drone intake is vendor-neutral observation ingestion only; it does not provide aircraft control, image hosting, or computer-vision inference.
- MAVLink bridge is read-only telemetry-only; `.tlog` parsing and UDP live parsing remain future/reviewed work.
- Hawaii cohort expansion (10-20 strict timeline-separated cases) not yet complete
- WA carcass replay exposes the need for tide/current drift support before down-current corridor recommendations can become data-backed
- Greater Recife replay exposes missing Pernambuco regional-pack, reef-barrier, tide/current, turbidity, human-exposure, and monitoring-program ingestion support
- Michaelmas Island replay shows high WA spearfishing/offshore surveillance context even before post-incident signals, with missing live weather/ocean/sighting sources.
- Lovers Point replay shows carcass and closure surveillance context while drift direction remains unavailable until tide/current fixture support exists.

## Next Planned Phase

- Phase 25C: Drone Operator Observation Console
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

## Validation Counts (Latest Phase 25B Local Run)

- Focused MAVLink bridge tests: `11 passed`
- Focused drone-ingestion tests: `10 passed, 1 warning`
- Focused Panama City replay tests: `3 passed`
- Full backend tests: `253 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- Secret scan on changed files: no credential values; variable/config names only for `AI1SAD_DRONE_API_KEY`
- Prohibited-language scan: guardrail-only matches in docs

## Current Review Item

- Michaelmas Island Albany WA 2026 active-event replay reviewed and committed.
- Lovers Point Pacific Grove Whale Carcass 2026 active-event replay reviewed and committed.
- Both case studies use existing replay/provider layers only and do not add scoring-weight retunes, live scraping, auth/billing, or frontend runtime changes.
- Phase 25B is in local review and not staged or committed. Phase 25C must remain future work only until this bridge is reviewed and committed.

## Recent Important Commits

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
