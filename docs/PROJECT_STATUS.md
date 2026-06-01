# Project Status

## Current Snapshot

- Current phase number: Phase 23 (planned)
- Latest completed phase: Phase 22 (Hawaii Habitat Mapping Adapter)
- Latest commit hash: `e880846623b9b45a5891c6f2264dea60070e6790`
- Repo status: clean working tree on `main`

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

- Tide-state adapter not yet integrated
- Current-direction/speed adapter not yet integrated
- Turbidity/water-clarity adapter not yet integrated
- Live surf-line/lifeguard observation ingestion not yet integrated
- Live sightings ingestion pipeline still limited
- Hawaii cohort expansion (10-20 strict timeline-separated cases) not yet complete

## Next Planned Phase

- Phase 23: Tide, Current & Nearshore Water-Movement Adapter
- Planning details: see [NEXT_PHASE.md](NEXT_PHASE.md)

## Exact Next Codex Resume Prompt

Use this as the next prompt anchor:

```text
Phase 23: Tide, Current & Nearshore Water-Movement Adapter

Repo:
F:\shark-attack-api

Goal:
Add a static/offline-first tide and nearshore current adapter for AI1SAD as bounded environmental context.

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

## Validation Counts (Latest Phase 22 Run)

- Focused habitat tests: `9 passed`
- Focused replay regression tests: `34 passed`
- Full backend tests: `194 passed`
- MkDocs build: passed
- Secret scan: no matches
- Prohibited-language scan: guardrail/disclaimer-only matches

## Recent Important Commits

- `e880846` Add Hawaii habitat mapping adapter
- `5d5aa79` Add Hawaii signal gap analysis
- `941416c` Add Cromwells Beach Hawaii replay case study
- `9e3d112` Add bounded kelp forest habitat signal layer
- `a9a8542` Harden public API query handling and error metadata
- `3f6ce69` Fix frontend live-data trust and replay selection handling
- `ba6d3df` Integrate AI1SAD brand assets across platform
- `90e540e` Add one-click local demo launcher
