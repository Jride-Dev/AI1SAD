# Next Phase

## Phase 25D: Observation Media References and Analyst Review Queue

## Objective

Add a bounded workflow for attaching media references to human-entered observations and routing those observations through an analyst review queue.

Phase 25D should build on Phase 25C's Drone Operator Console without changing aircraft-control boundaries.

## Constraints

- Do not tune scoring weights
- Do not add attack-probability language
- Do not infer shark intent
- Do not add autonomous takeoff, landing, waypoint, or offboard-control commands
- Do not transmit MAVLink commands
- Do not add DJI-specific dependencies
- Do not add computer vision
- Do not upload or host media until storage, privacy, and retention rules are reviewed
- Do not change auth/billing
- Do not commit until review

## Phase 25C Completion Note

Phase 25C adds a local Drone Operator Console:

- frontend route: `http://localhost:5174/drone-console`
- mission selector and known-mission fetch workflow
- human-entered observation form
- no-sighting patrol caveat
- provisional species-copy guidance
- recent map-ready feed panel
- explicit live-mode backend error handling
- existing drone observation endpoints reused
- no aircraft control

## Planned Scope

1. Define media-reference metadata fields for observations
2. Add analyst review queue states and filters
3. Preserve public/private media-reference boundaries
4. Show queue-ready observations in a local analyst view
5. Keep media references as references only unless storage is explicitly designed
6. Add tests for private notes, media-reference filtering, and review-state transitions

## Source Inputs

- Existing drone mission and observation APIs
- Phase 25C console-submitted observations
- Existing public-safe surveillance feed
- Existing `media_reference` field

## Bounded Behavior Rules

- Media references are metadata, not uploaded evidence, until a reviewed storage design exists.
- Analyst review may change review status and public summary metadata.
- Analyst review must not infer species as official classification without an official or qualified source.
- No observation media workflow may control aircraft.
- No media reference may expose private filesystem paths in public output.

## Recommended Execution Order

1. Review current observation contract and public filtering
2. Design analyst-review states and allowed transitions
3. Add queue API or reuse existing endpoints if sufficient
4. Add frontend queue surface
5. Update drone docs and safety docs
6. Run backend, frontend, docs, secret, and prohibited-language validation

## Validation Expectations

- focused drone observation tests
- focused analyst queue tests if backend changes are added
- frontend tests
- frontend build
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

## Review Gate

Do not begin Phase 25D until Phase 25C has been reviewed and either committed or explicitly set aside.
