# Next Phase

## Phase 25F: UAV Operator Feedback Intake and Field Requirements Tracker

## Objective

Create a structured feedback intake and field-requirements tracker for UAV operators, lifeguards, coastal authorities, and shark-surveillance teams who review or test AI1SAD.

Do not start this phase automatically. Phase 25F begins only after Phase 25E is reviewed and committed.

## Current Baseline

Phase 25E should leave AI1SAD with:

- `docs/UAV_OPERATOR_RESEARCH_BRIEF.md` — comprehensive operator-facing research brief
- `docs/UAV_COMPATIBILITY_MATRIX.md` — shorter companion compatibility table
- Updated README and MkDocs navigation
- No code changes

## Planned Scope (Future Phase)

1. Create a feedback template for UAV operators to report:
   - which drone platforms they use
   - what telemetry is available
   - what observation fields they currently record
   - what is missing from AI1SAD for their workflow
   - what privacy or airspace restrictions they face
2. Create a field-requirements tracker that maps operator needs to AI1SAD capabilities:
   - supported today
   - needs documentation only
   - needs future implementation
   - out of scope
3. Document common pain points from real-world drone patrol workflows.
4. Update the UAV Operator Research Brief with operator-validated field requirements.

## Safety Boundaries

- Do not add flight-control code.
- Do not add cloud storage.
- Do not add external media APIs.
- Do not add computer vision.
- Do not infer species or sightings from media.
- Do not change scoring weights.
- Do not modify replay outputs.

## Validation Expectations

- mkdocs build
- README link/image check if README changes
- secret scan
- prohibited-language scan
- backend/frontend tests only if code changes occur

## Review Gate

Stop before committing unless explicitly asked to commit Phase 25F work.
