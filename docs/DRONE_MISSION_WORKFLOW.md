# Drone Mission Workflow

## Operator Flow

1. A human operator starts a mission record.
2. The operator or local integration posts telemetry points.
3. The operator posts observation records with review status and evidence metadata.
4. AI1SAD converts eligible observations into existing operational signals.
5. The surveillance feed returns map-ready items, surveillance scoring, and alert evaluation.
6. The operator completes the mission.

## Mission Types

- `shoreline_parallel_sweep`
- `reef_gap_focus_scan`
- `channel_mouth_pass`
- `post_sighting_focus_area`
- `carcass_event_buffer_zone`
- `kelp_edge_focus_scan`
- `offshore_island_focus_scan`
- `manual_observation_patrol`

## Human Approval

Every mission is recorded as `human_approved=true` and `autonomous_flight_control=false`.

AI1SAD can recommend a patrol pattern, but it does not issue flight-control commands or route execution instructions.

The MAVLink telemetry bridge may post read-only telemetry points into the mission workflow when explicitly enabled. It does not create or modify missions beyond the existing human-approved mission record.

## Review Status

- `unreviewed`
- `operator_reviewed`
- `analyst_reviewed`
- `confirmed`
- `rejected`

Rejected observations are not used in public active-observation or feed outputs.
