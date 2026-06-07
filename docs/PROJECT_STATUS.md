# Project Status

## Current Snapshot

- Current phase number: Phase 25 (Live Sightings & Surf-Line Observation Ingestion Adapter)
- Latest completed committed phase: Phase 24 (Water Clarity & Turbidity Adapter)
- Latest completed local phase: Phase 24 (Water Clarity & Turbidity Adapter)
- Latest commit hash: current `HEAD` after the Phase 24 commit; verify with `git log --oneline -1`
- Repo status: clean after Phase 24 commit; push pending

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
- Hawaii cohort expansion (10-20 strict timeline-separated cases) not yet complete
- WA carcass replay exposes the need for tide/current drift support before down-current corridor recommendations can become data-backed
- Greater Recife replay exposes missing Pernambuco regional-pack, reef-barrier, tide/current, turbidity, human-exposure, and monitoring-program ingestion support

## Next Planned Phase

- Phase 25: Live Sightings & Surf-Line Observation Ingestion Adapter
- Planning details: see [NEXT_PHASE.md](NEXT_PHASE.md)

## Exact Next Codex Resume Prompt

Use this as the next prompt anchor after Phase 24 review/commit:

```text
Phase 25: Live Sightings & Surf-Line Observation Ingestion Adapter

Repo:
F:\shark-attack-api

Goal:
Add reviewed, source-attributed sightings and surf-line/lifeguard observation ingestion for AI1SAD as bounded operational observation context.

Constraints:
- do not tune scoring weights
- do not add attack-probability language
- do not infer shark intent
- no live scraping
- no auth/billing changes
- do not commit until review
```

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

## Validation Counts (Latest Phase 24 Run)

- Focused water clarity/turbidity tests: `11 passed`
- Focused Cromwell replay regression tests: `38 passed`
- Full backend tests: `222 passed, 2 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- Secret scan: no matches
- Prohibited-language scan: safety-rule/guardrail-only matches

## Current Review Item

- Phase 24 Hawaii water clarity/turbidity adapter is committed locally.
- Static/offline Oahu visibility baselines are wired through warning, surveillance, alerts, explainability, replay, and docs.
- Cromwell replay remains timeline-safe and is treated as a regression case only.
- No live scraping, scoring-weight retuning, auth/billing, or frontend runtime changes were added.

## Recent Important Commits

- `HEAD` Add Hawaii water clarity and turbidity adapter
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
