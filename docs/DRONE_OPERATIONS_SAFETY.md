# Drone Operations Safety

AI1SAD drone integration is strictly advisory and observational.

## Safety Boundaries

- Drone write endpoints are disabled unless `DRONE_INGEST_ENABLED=true`.
- No autonomous takeoff
- No autonomous landing
- No waypoint execution
- No offboard flight control
- No aircraft-control commands in public or internal API responses
- No vendor-specific command dependencies
- MAVLink bridge support is telemetry-only and must not transmit MAVLink commands.

## Interpretation Rules

- A drone sighting is source-attributed observation metadata.
- Review status affects confidence.
- Probable species is not official taxonomy unless a source says so.
- Observed behavior is preserved as reported and does not imply intent.
- A no-sighting patrol result does not establish safety.

## Operational Use

Recommended patterns such as `shoreline_parallel_sweep` and `post_sighting_focus_area` are planning labels for human operators. They are not executable flight plans.
