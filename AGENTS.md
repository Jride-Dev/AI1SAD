# AGENTS.md - AI1SAD Project Instructions

## Project Identity

AI1SAD is a marine operational-intelligence platform for shark-risk awareness, coastal surveillance prioritization, replay analysis, and drone-assisted observation workflows.

It is not an individual attack-prediction system.

It must remain:

* bounded
* explainable
* evidence-aware
* source-attributed
* operationally useful
* cautious about uncertainty
* safe for public-facing use

The system may recommend surveillance attention and human-reviewed operational actions.

The system must never claim certainty where evidence does not support it.

---

## Start-of-Task Workflow

At the beginning of each task:

1. Read:

   * `docs/PROJECT_STATUS.md`
   * `docs/NEXT_PHASE.md`

2. Inspect:

   * `git status`
   * `git diff --stat`

3. Follow the user’s current request.

4. Do not automatically begin future phases.

5. Do not recursively re-read instructions, re-run completed work, or start another task after the current task finishes.

6. When the requested work is complete:

   * update documentation
   * run validation
   * report results
   * stop before staging or committing unless explicitly instructed otherwise

---

## No-Loop Rule

Do not create self-perpetuating work loops.

Never:

* automatically start the next phase
* repeatedly regenerate documentation without a concrete change
* repeatedly run the same validation suite after it already passed
* recursively audit the entire repo unless explicitly asked
* create new tasks for yourself after finishing the requested task
* commit, push, deploy, or begin another feature without user direction

Complete one bounded task, validate it, report it, and stop.

If a validation failure occurs:

* diagnose the direct cause
* patch only the relevant issue
* rerun the affected validation
* report the result
* stop if further work would expand scope

---

## Core Safety Boundaries

Never add language claiming:

* attack probability
* probability of an individual shark attack
* certainty that a shark attack will occur
* inferred shark intent
* rogue-shark narratives
* certainty from incomplete evidence

Use operational language:

* surveillance priority
* warning score
* activity hazard
* habitat context
* environmental context
* recent interaction
* biological-event context
* uncertainty
* confidence
* freshness
* recommended monitoring pattern

Do not tune scoring weights around one incident to make a replay look more successful.

Do not contaminate strict pre-incident replays with hindsight.

Do not invent missing:

* sightings
* tide values
* current values
* weather values
* turbidity values
* drift directions
* biological events
* species identifications
* prey migrations
* closures
* telemetry

Mark missing values honestly.

---

## Source Provenance Rules

Every incident, signal, and species assessment must preserve provenance.

Possible provenance types:

* official agency notice
* official government source
* agency preliminary assessment
* source-attributed media report
* project-owner analyst visual assessment
* operator visual assessment
* fixture-based demo value
* static baseline dataset
* hypothetical sensitivity scenario
* confirmed external source

Do not silently convert preliminary, provisional, analyst-assessed, or hypothetical information into confirmed facts.

Species handling must distinguish:

* `official_species_classification`
* `probable_species`
* `species_assessment_source`
* `species_confidence`
* `evidence_basis`
* `taxonomy_confidence`

Probable species metadata should normally affect explainability only unless existing bounded model rules explicitly support suitability context.

---

## Replay Case-Study Rules

Every replay case study should clearly separate:

1. Strict pre-incident replay

   * only timeline-valid information available before the incident

2. Quiet-day comparison

   * same location, season, activity, and baseline context without incident-specific signals

3. Post-incident operational update

   * later confirmed events, sightings, closures, or advisories

4. Hypothetical sensitivity run

   * clearly labeled hypothetical
   * never mixed into verified history

Every replay should include:

* coordinates
* timestamps
* outcome
* activity context
* regional pack
* warning score
* activity hazard score
* surveillance priority score
* confidence breakdown
* dominant factors
* missing sources
* explainability summary
* recommended operational patterns
* version metadata
* disclaimer

Historical sightings must be evaluated relative to replay scenario time, not current wall-clock time.

Do not assume separate incidents involve the same individual shark unless a source explicitly supports that conclusion.

---

## Existing Major Systems

AI1SAD currently includes:

* historical incident database
* surveillance engine
* warning engine
* alert engine
* replay engine
* quiet-day comparisons
* explainability engine
* provider health
* regional packs
* signal broker
* human exposure provider
* biological-event provider
* vessel/fishing provider
* SST context
* kelp-forest habitat layer
* Hawaii habitat mapping adapter
* Hawaii tide/current context adapter
* Hawaii water-clarity/turbidity adapter
* replay library
* MkDocs documentation portal
* branded frontend dashboard
* operational Leaflet map
* local demo environment
* one-click local launcher
* vendor-neutral drone observation intake MVP
* read-only MAVLink telemetry bridge
* Panama City drone-observation replay case study

---

## Drone-System Safety Boundaries

AI1SAD drone support is currently observation-ingestion only.

The system may:

* create drone mission records
* ingest telemetry
* ingest operator observations
* ingest analyst-reviewed observations
* ingest no-sighting patrol outcomes
* recommend surveillance patterns
* return map-safe observation feeds
* update surveillance priority
* provide explainability

The system must not:

* arm or disarm aircraft
* initiate takeoff
* initiate landing
* upload waypoints
* change waypoints
* send MAVLink commands
* expose flight-control APIs
* use offboard control
* autonomously fly aircraft
* control DJI aircraft directly
* infer sightings from telemetry alone
* treat no-sighting patrols as proof of safety

All drone operations require human approval and human-operated flight control.

Required invariant:

```txt
AI1SAD recommends missions.
Humans approve missions.
Drone operators fly missions.
AI1SAD ingests observations.
```

Drone write endpoints must remain disabled by default unless explicitly enabled through configuration.

Current configuration gate:

```txt
DRONE_INGEST_ENABLED=false
```

Public drone feeds must never expose:

* operator IDs
* internal notes
* analyst notes unless explicitly public-safe
* credentials
* private media paths
* raw stack traces
* hidden source metadata

---

## Provider Rules

Providers should default to static/offline fixtures unless live integration is explicitly requested.

Do not add:

* scraping
* unofficial hidden network calls
* paid APIs
* live external dependencies
* vendor lock-in

unless the user explicitly approves them.

Every provider must include:

* source metadata
* freshness
* confidence
* pack association
* public/private visibility
* safe missing-data behavior

Every provider must degrade gracefully.

A provider failure must not crash public endpoints.

Public failure output should remain coarse:

* `provider_unavailable`
* `fetch_failed`
* `missing_source`
* `stale_data`

Do not expose raw exception messages or stack traces publicly.

---

## Frontend Trust Rules

Live mode must fail closed.

When:

```txt
VITE_AI1SAD_USE_MOCKS=false
```

the frontend must not silently substitute mock data after:

* network failures
* CORS failures
* backend 500 responses
* malformed JSON
* malformed payloads

Mock data is allowed only when explicitly enabled.

The UI must clearly label:

* mock demo data source
* live backend data source
* backend unavailable state

Do not duplicate scoring logic in the frontend.

The frontend renders backend or mock values only.

---

## Documentation Gate

Documentation is mandatory.

Before stopping for review, update all documentation affected by the current task.

Always inspect and update when relevant:

* `docs/PROJECT_STATUS.md`
* `docs/NEXT_PHASE.md`
* `docs/CURRENT_DATA_SOURCES.md`
* `docs/PROVIDER_HEALTH.md`
* `docs/EXPLAINABILITY_ENGINE.md`
* `docs/REGIONAL_PACKS.md`
* `docs/REPLAY_LIBRARY.md`
* `mkdocs.yml`

For drone-related work, also inspect:

* `docs/DRONE_OBSERVATION_INGESTION.md`
* `docs/DRONE_MISSION_WORKFLOW.md`
* `docs/DRONE_DATA_CONTRACT.md`
* `docs/DRONE_OPERATIONS_SAFETY.md`
* `docs/MAVLINK_TELEMETRY_BRIDGE.md`
* `docs/MAVLINK_LOCAL_DEMO.md`
* `docs/MAVLINK_SAFETY_BOUNDARIES.md`

For case studies, also update:

* case-study Markdown page
* replay JSON artifact
* factor-summary JSON artifact
* heatmap SVG where supported
* replay-library registry
* replay-library docs
* MkDocs navigation
* project status
* next phase

`PROJECT_STATUS.md` must remain the durable handoff file.

It should include:

* latest completed phase
* current in-progress phase
* latest committed checkpoint
* major completed systems
* active safety boundaries
* current validation counts
* known gaps
* uncommitted work summary
* next recommended action

`NEXT_PHASE.md` must include:

* next phase title
* scope
* likely files
* safety boundaries
* validation requirements
* explicit stop-before-commit gate

---

## Git Discipline

Do not stage, commit, push, deploy, or rewrite history unless the user explicitly requests it.

Before commit:

* inspect `git status`
* inspect `git diff --stat`
* inspect substantive deletions
* confirm no unrelated files are included
* run validation
* report findings

Prefer logical commits.

Split unrelated work into separate commits.

Examples:

* security fix
* replay case study
* provider integration
* documentation-only update
* frontend trust fix
* dependency patch

Do not:

* squash without request
* amend without request
* force push
* stage `.env`
* stage cache files
* stage generated build output
* stage local DB files
* stage raw private datasets
* stage private notes
* stage secrets

---

## Ignored / Local-Only Files

Do not stage:

* `.env`
* `data/`
* `site/`
* `frontend/dist/`
* `frontend/node_modules/`
* `frontend/tsconfig.tsbuildinfo`
* `.mkdocs-demo.*`
* `.vscode/`
* `*.code-workspace`
* local databases
* caches
* temporary exports
* temporary logs

---

## Local Demo

Use:

```txt
start_ai1sad_demo.bat
```

Stop with:

```txt
stop_ai1sad_demo.bat
```

Expected URLs:

* Frontend: [http://localhost:5174](http://localhost:5174/)
* FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* MkDocs: [http://localhost:8001](http://localhost:8001/)

FretTrack may occupy port `5173`, so AI1SAD uses `5174`.

---

## Validation Requirements

Run the relevant focused tests first.

Then run the appropriate full validation suite.

Typical backend validation:

```txt
python -m pytest -q
```

or the known local Windows interpreter where required:

```txt
F:\Python310\python.exe -m pytest -q
```

Frontend:

```txt
cd frontend
npm test
npm run build
npm audit --audit-level=high
```

MkDocs:

```txt
mkdocs build
```

Also run:

* secret scan
* prohibited-language scan
* JSON parse checks for replay artifacts
* SVG parse checks for heatmaps
* broken-link or missing-page check where available

If RTK wrappers return nonzero due only to the known MkDocs Material advisory, verify with direct:

```txt
mkdocs build
```

Do not treat a passing direct MkDocs build as failed solely because the wrapper dislikes an upstream advisory.

---

## Dependency Rules

Do not run:

```txt
npm audit fix --force
```

Use targeted dependency updates only.

Inspect:

* affected package
* dependency path
* runtime vs dev dependency
* patched version
* lockfile churn
* breaking-change risk

Document security patches in:

* `docs/DEPENDENCY_SECURITY_REVIEW.md`
* `docs/PROJECT_STATUS.md`

---

## Current Next Phase

Read:

```txt
docs/NEXT_PHASE.md
```

Do not rely on this file section alone because the repo handoff may have advanced.

The likely next planned work after Phase 25B is:

```txt
Phase 25C: Drone Operator Observation Console
```

Safety invariant:

* human-reviewed observation workflows only
* no outbound commands
* no autonomous aircraft control

---

## Required End-of-Task Report

At the end of each task, report:

1. What changed
2. What did not change
3. Files added
4. Files modified
5. Validation run
6. Test counts
7. Security scan results
8. Prohibited-language scan results
9. Documentation updated
10. Git status
11. Whether anything was staged or committed
12. Any remaining risks or gaps

## MkDocs Portal Update Rule

MkDocs is part of the product. Keep it current during every task.

Whenever a task adds, removes, renames, or materially updates documentation:

1. Update `mkdocs.yml`.
2. Add every new public documentation page to the appropriate navigation section.
3. Remove or correct stale navigation entries.
4. Verify renamed files do not leave broken links.
5. Update cross-links in existing docs where appropriate.
6. Confirm new case studies appear under Replay & Case Studies.
7. Confirm new provider pages appear under Data Sources / Providers.
8. Confirm drone and MAVLink pages appear under Drone Operations.
9. Confirm status pages remain visible:

   * `docs/PROJECT_STATUS.md`
   * `docs/NEXT_PHASE.md`

Before stopping for review, run:

```bash
mkdocs build
```
For the current drone intake and MAVLink work, Codex should confirm these are present in mkdocs.yml:
Drone Operations
- Drone Observation Ingestion
- Drone Mission Workflow
- Drone Data Contract
- Drone Operations Safety
- MAVLink Telemetry Bridge
- MAVLink Local Demo
- MAVLink Safety Boundaries

Replay & Case Studies
- NSA Panama City Florida 2026

Project
- Project Status
- Next Phase
Report:

* every documentation page added
* every documentation page modified
* every `mkdocs.yml` navigation change
* MkDocs build result
* any missing-page or broken-link warnings

Do not leave new documentation outside MkDocs navigation unless it is explicitly internal-only.
Do not stop for review while MkDocs navigation is stale.

Then stop.

Do not automatically begin the next phase.
