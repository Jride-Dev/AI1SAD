# Next Phase

## Phase 25G: UAV Feedback Review Dashboard and Requirements Prioritization

## Objective

Add a review dashboard for UAV operator feedback records and turn submitted workflow notes into prioritized requirements without treating feedback as live surveillance data.

Target full working-version launch: September 7, 2026.

AI1SAD is targeting a full working-version launch on September 7, 2026. Current development is focused on UAV operator workflows, evidence metadata, replay explainability, and public-safe surveillance outputs.

Do not start this phase automatically. Phase 25G begins only after Phase 25F is reviewed and committed.

## Current Baseline

Phase 25F should leave AI1SAD with:

- `POST /api/v1/uav/operator-feedback`
- `GET /api/v1/uav/operator-feedback`
- `PATCH /api/v1/uav/operator-feedback/{feedback_id}/status`
- frontend route `/uav-feedback`
- research-only feedback records
- public/private field filtering
- validation for enums, note lengths, unsafe contact references, public-summary contact leakage, and obvious secrets
- no sightings, warnings, public alerts, replay facts, surveillance feed entries, scoring changes, drone operations, SDK integrations, media upload, cloud storage, computer vision, or MAVLink command behavior

## Planned Scope

1. Add a dedicated feedback review dashboard.
2. Show feedback cards grouped by review status.
3. Add requirements prioritization fields:
   - priority
   - effort estimate
   - safety impact
   - workflow impact
   - dependency notes
4. Add filters for:
   - region
   - organization type
   - telemetry availability
   - media workflow
   - requirements tag
5. Keep private contact references and private notes out of public-facing views.
6. Update docs with a requirements triage workflow.

## Safety Boundaries

- Do not convert feedback into live observations.
- Do not create sightings from feedback.
- Do not create warnings or public alerts from feedback.
- Do not alter scoring weights.
- Do not modify replay outputs.
- Do not add cloud storage.
- Do not add media upload.
- Do not add computer vision.
- Do not add drone SDK integrations.
- Do not add autonomous flight control.
- Do not add MAVLink command/control behavior.
- Do not imply endorsement from any agency/operator.

## Validation Expectations

- focused UAV feedback tests
- full backend tests
- frontend tests
- frontend build
- npm audit high
- mkdocs build
- README link/image check
- secret scan
- prohibited-language scan
- git diff --check

## Review Gate

Stop before committing unless explicitly asked to commit Phase 25G work.
