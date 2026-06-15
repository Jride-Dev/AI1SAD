# Drone Mission Workflow

## Operator Flow

1. A human operator starts a mission record.
2. The operator or local integration posts telemetry points.
3. The operator posts observation records with review status and evidence metadata, either through the API or the local Drone Operator Console.
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

The Drone Operator Console may display mission and telemetry context, then submit human-entered observations to the existing observation endpoint. It does not communicate with aircraft.

## Review Status

- `unreviewed`
- `operator_reviewed`
- `analyst_reviewed`
- `confirmed`
- `rejected`

Rejected observations are not used in public active-observation or feed outputs.

## Analyst Review

Phase 25D-A adds metadata-only analyst review as an optional post-ingestion step. An analyst can update review status, outcome, public summary, and private notes on an existing observation via the PATCH endpoint:

```text
PATCH /api/v1/drone/missions/{mission_id}/observations/{observation_id}
```

The Drone Operator Console surfaces observations needing review. Review fields are annotations only; they do not change the original observation type or create new sightings.

See [Observation Analyst Review](OBSERVATION_ANALYST_REVIEW.md).

## Local Console Workflow

Open:

```text
http://localhost:5174/drone-console
```

Use the console to:

- select or fetch a known mission
- review mission ID, drone ID, status, and telemetry context when available
- enter a source-attributed observation
- record no-sighting patrols with the explicit caveat that they do not prove safety
- review recent public-safe feed items for the selected mission

Drone write endpoints still require:

```text
DRONE_INGEST_ENABLED=true
```
