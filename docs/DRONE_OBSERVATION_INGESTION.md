# Drone Observation Ingestion

Phase 25A adds a vendor-neutral intake path for human-operated coastal-surveillance drone observations.

This is an observation-ingestion layer. AI1SAD records mission, telemetry, and observation metadata, then converts eligible public observations into existing signal, surveillance, explainability, alert, and replay flows. It does not command aircraft.

Phase 25B adds a read-only MAVLink telemetry bridge that can replay telemetry into the existing telemetry endpoint. It does not add aircraft command/control or create observations from telemetry alone.

Phase 25C adds a local Drone Operator Console at `http://localhost:5174/drone-console`. The console is a human-facing frontend for the same mission, observation, active-observation, and surveillance-feed routes. It does not add aircraft control or duplicate backend scoring logic.

Phase 25D-A adds metadata-only analyst review fields and a PATCH endpoint for updating review status, outcome, private notes, and public summary on existing observations.

## Scope

- Human operator mission records
- Timestamped telemetry points
- Source-attributed observations
- Public/private filtering
- Reviewed sighting handling
- Map-ready surveillance feed output
- Replay fixture support for historical drone observations
- Local operator-console workflow for human-entered observations

## Non-Scope

- Autonomous takeoff, landing, waypoint execution, or offboard control
- DJI-specific dependencies
- MAVLink dependencies
- Computer-vision inference
- Image hosting
- Autonomous operator-console flight actions
- Auth or billing
- Broad scoring-weight changes

Phase 25B keeps MAVLink dependency support out of runtime code; fixture replay uses normalized JSONL records.

## Observation Semantics

Drone observations are operational signals. A single unreviewed sighting can raise surveillance attention modestly, while reviewed or confirmed observations can carry more operational weight through the existing sighting logic.

A no-sighting patrol result is not proof of safety. It only narrows uncertainty inside the documented coverage area, patrol window, and visibility context.

Probable species can be stored with provenance and confidence. It remains metadata unless existing regional suitability rules independently use a bounded species context.

The console supports `other` as a generic observation type for reviewed field notes that do not fit the structured categories. `other` remains a generic observation signal and does not create a shark sighting.

## API Routes

```text
POST /api/v1/drone/missions
GET /api/v1/drone/missions/{mission_id}
POST /api/v1/drone/missions/{mission_id}/telemetry
POST /api/v1/drone/missions/{mission_id}/observations
GET /api/v1/drone/missions/{mission_id}/observations
PATCH /api/v1/drone/missions/{mission_id}/observations/{observation_id}
POST /api/v1/drone/missions/{mission_id}/complete
GET /api/v1/drone/active-observations
GET /api/v1/drone/surveillance-feed
```

Public responses filter internal notes and expose `flight_control.commands_exposed=false`.

## Ingestion Gate

Drone write endpoints are disabled by default. Set `DRONE_INGEST_ENABLED=true` in a reviewed local or deployment environment before accepting mission, telemetry, observation, or completion writes.

Public read endpoints remain available for sanitized active-observation and surveillance-feed output.

## Console Route

```text
http://localhost:5174/drone-console
```

The console uses explicit mock/demo fixtures only when frontend mock mode is enabled. In live mode, backend failures and validation errors remain visible and do not silently fall back to mock data.
