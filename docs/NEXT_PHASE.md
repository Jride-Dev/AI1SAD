# Next Phase

## Phase 25C: Drone Operator Observation Console

## Objective

Add a local operator console for human-reviewed drone observations using the existing AI1SAD drone mission, telemetry, observation, and surveillance-feed APIs.

## Constraints

- Do not tune scoring weights
- Do not add attack-probability language
- Do not infer shark intent
- Do not add autonomous takeoff, landing, waypoint, or offboard-control commands
- Do not transmit MAVLink commands
- Do not add DJI-specific dependencies
- Do not add computer vision
- Do not change auth/billing
- Do not commit until review

## Phase 25B Completion Note

Phase 25B adds a read-only MAVLink telemetry bridge:

- deterministic JSONL fixture replay
- safe Panama City shoreline patrol telemetry fixture
- telemetry normalization and validation
- mocked API submission tests
- disabled-by-default bridge and UDP modes
- no flight-control routes or commands

Operator-console UI remains future work.

## Planned Scope

1. Display active mission telemetry from existing APIs
2. Let a human operator submit reviewed observations
3. Show public-safe surveillance feed items
4. Preserve no-sighting patrol semantics
5. Keep all write actions behind existing backend gates
6. Add focused tests proving no aircraft-control commands are exposed

## Source Inputs

- Existing AI1SAD drone mission and observation APIs
- Existing AI1SAD surveillance-feed output
- Existing map-ready feed fields

The console should not communicate with aircraft directly.

## Bounded Behavior Rules

- Operators submit source-attributed observations only.
- Telemetry remains context and should not create a sighting.
- Do not infer species or behavior from telemetry alone.
- Do not tune scoring weights around Panama City or any single case.

## Recommended Execution Order

1. Console requirements and safety design
2. Read-only mission/telemetry/feed views
3. Human-reviewed observation form
4. Tests for safe filtering and no command exposure
5. Docs and validation sweep

## Validation Expectations

- focused drone operator console tests
- focused MAVLink bridge regression tests
- focused drone intake regression tests
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

Frontend tests/build should run if frontend runtime files are touched.

## Review Gate

Do not commit until review.

## Current Interruption Note

Phase 25B is local work in review until committed. Begin Phase 25C only after Phase 25B is reviewed and committed.
