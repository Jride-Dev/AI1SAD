# Drone Operations Safety

AI1SAD drone integration is strictly advisory and observational.

Phase 25C adds a Drone Operator Console for human-entered observations. It is a frontend intake surface over existing drone APIs and does not change aircraft-safety boundaries.

Phase 25D-A adds metadata-only analyst review fields. These are annotations on existing observations and do not change aircraft-safety boundaries.

## Safety Boundaries

- Drone write endpoints are disabled unless `DRONE_INGEST_ENABLED=true`.
- No autonomous takeoff
- No autonomous landing
- No waypoint execution
- No offboard flight control
- No aircraft-control commands in public or internal API responses
- No vendor-specific command dependencies
- MAVLink bridge support is telemetry-only and must not transmit MAVLink commands.
- The Drone Operator Console must not expose arming, takeoff, landing, waypoint, mission-upload, offboard-control, or MAVLink command actions.
- Analyst review fields are metadata-only; AI1SAD does not fetch, host, or analyze media
- `analyst_notes_private`, `analyst_reviewer_role`, and `analyst_reviewed_at` are excluded from public output

## Interpretation Rules

- A drone sighting is source-attributed observation metadata.
- Review status affects confidence.
- Probable species is not official taxonomy unless a source says so.
- Observed behavior is preserved as reported and does not imply intent.
- A no-sighting patrol result does not establish safety.
- Species guesses entered through the console are provisional unless confirmed by an official source or qualified review.

## Operational Use

Recommended patterns such as `shoreline_parallel_sweep` and `post_sighting_focus_area` are planning labels for human operators. They are not executable flight plans.

Console safety copy:

```text
AI1SAD records human observations and recommends surveillance attention. It does not control aircraft or predict individual shark attacks.
```

No-sighting patrol copy:

```text
No-sighting patrols reduce uncertainty only within the observed patrol area, time window, and visibility conditions. They do not prove an area is safe.
```
