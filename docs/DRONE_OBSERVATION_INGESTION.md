# Drone Observation Ingestion

Phase 25A adds a vendor-neutral intake path for human-operated coastal-surveillance drone observations.

This is an observation-ingestion layer. AI1SAD records mission, telemetry, and observation metadata, then converts eligible public observations into existing signal, surveillance, explainability, alert, and replay flows. It does not command aircraft.

## Scope

- Human operator mission records
- Timestamped telemetry points
- Source-attributed observations
- Public/private filtering
- Reviewed sighting handling
- Map-ready surveillance feed output
- Replay fixture support for historical drone observations

## Non-Scope

- Autonomous takeoff, landing, waypoint execution, or offboard control
- DJI-specific dependencies
- MAVLink dependencies
- Computer-vision inference
- Image hosting
- Auth or billing
- Broad scoring-weight changes

## Observation Semantics

Drone observations are operational signals. A single unreviewed sighting can raise surveillance attention modestly, while reviewed or confirmed observations can carry more operational weight through the existing sighting logic.

A no-sighting patrol result is not proof of safety. It only narrows uncertainty inside the documented coverage area, patrol window, and visibility context.

Probable species can be stored with provenance and confidence. It remains metadata unless existing regional suitability rules independently use a bounded species context.

## API Routes

```text
POST /api/v1/drone/missions
GET /api/v1/drone/missions/{mission_id}
POST /api/v1/drone/missions/{mission_id}/telemetry
POST /api/v1/drone/missions/{mission_id}/observations
GET /api/v1/drone/missions/{mission_id}/observations
POST /api/v1/drone/missions/{mission_id}/complete
GET /api/v1/drone/active-observations
GET /api/v1/drone/surveillance-feed
```

Public responses filter internal notes and expose `flight_control.commands_exposed=false`.

## Ingestion Gate

Drone write endpoints are disabled by default. Set `DRONE_INGEST_ENABLED=true` in a reviewed local or deployment environment before accepting mission, telemetry, observation, or completion writes.

Public read endpoints remain available for sanitized active-observation and surveillance-feed output.
