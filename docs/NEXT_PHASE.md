# Next Phase

## Phase 25B: MAVLink Telemetry Bridge

## Objective

Plan a narrow telemetry bridge for future MAVLink-compatible drone telemetry ingestion while keeping AI1SAD strictly out of aircraft command and control.

## Constraints

- Do not tune scoring weights
- Do not add attack-probability language
- Do not infer shark intent
- Do not add autonomous takeoff, landing, waypoint, or offboard-control commands
- Do not add DJI-specific dependencies
- Do not change auth/billing
- Do not commit until review

## Phase 25A Completion Note

Phase 25A adds vendor-neutral human-operated drone observation intake:

- mission records
- telemetry point ingestion
- observation ingestion
- public-safe active observations and surveillance feed
- NSA Panama City fixture-based drone replay
- no flight-control routes or commands

MAVLink support is still future work.

## Planned Scope

1. Define a telemetry-only MAVLink bridge boundary
2. Accept pre-reviewed telemetry messages without command/control support
3. Map telemetry into existing `DroneTelemetryPoint` records
4. Keep `DRONE_INGEST_ENABLED` and any future bridge gate disabled by default
5. Add public/private filtering and bounded payload validation
6. Add focused tests proving no aircraft-control commands are exposed

## Official/Public Source Candidates

- MAVLink message specifications for telemetry-only fields
- Human-operated drone telemetry logs exported by operators
- Future local bridge adapters reviewed for safety and licensing

No bridge should send commands to an aircraft.

## Bounded Behavior Rules

- Telemetry is metadata/context and should not create high warning states by itself.
- Stronger effects still require reviewed observations or stacked environmental/activity context.
- Do not infer species or behavior from telemetry alone.
- Do not tune scoring weights around Panama City or any single case.

## Recommended Execution Order

1. Bridge safety design
2. Telemetry-only schema mapping
3. Disabled-by-default config gate
4. Unit tests for no command exposure
5. Docs and validation sweep

## Validation Expectations

- focused MAVLink telemetry bridge tests
- focused drone intake regression tests
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

Frontend tests/build can remain skipped if frontend files are unchanged.

## Review Gate

Do not commit until review.

## Current Interruption Note

Phase 25A adds vendor-neutral human-operated drone observation intake as a focused MVP. After Phase 25A review and commit, continue only with the telemetry-bridge planning in Phase 25B; MAVLink support remains future work until explicitly started.
