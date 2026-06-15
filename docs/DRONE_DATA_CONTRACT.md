# Drone Data Contract

## DroneMission

Required operational fields include:

- `mission_id`
- `drone_id`
- `operator_id`
- `operator_role`
- `region`
- `pack_id`
- `mission_type`
- `started_at`
- `ended_at`
- `status`
- `launch_location`
- `intended_area`
- `recommended_pattern`
- `human_approved`
- `autonomous_flight_control`
- `source`
- `visibility`
- `notes_public`

Internal mission notes are stored privately and removed from public responses.

## DroneTelemetryPoint

Read-only bridge records use the same telemetry contract as operator-submitted points.

- `mission_id`
- `drone_id`
- `timestamp`
- `latitude`
- `longitude`
- `altitude_m`
- `heading_deg`
- `groundspeed_mps`
- `battery_percent`
- `gps_fix_quality`
- `camera_heading_deg`
- `camera_pitch_deg`
- `source`
- `source_type`
- `public_visibility`
- bridge source: `mavlink_bridge`
- bridge source types: `fixture_replay`, `tlog_replay`, `udp_live`

Validation bounds:

- latitude: `-90` to `90`
- longitude: `-180` to `180`
- altitude: `-20` to `1000` meters
- heading/camera heading: `0` to `360`
- camera pitch: `-180` to `180`
- battery: `0` to `100`
- timestamp is required and must parse as a date/time

## DroneObservation

- `observation_id`
- `mission_id`
- `drone_id`
- `timestamp`
- `latitude`
- `longitude`
- `observation_type`
- `count`
- `estimated_length_m`
- `probable_species`
- `species_assessment_source`
- `species_confidence`
- `observed_behavior`
- `behavior_source`
- `evidence_type`
- `media_reference`
- `confidence`
- `review_status`
- `source`
- `source_type`
- `public_visibility`

Private analyst or internal notes are never exposed through public endpoints.

### Observation Types

- `shark_sighting`
- `unknown_large_marine_animal`
- `no_sighting_patrol_result`
- `carcass`
- `baitfish_congregation`
- `marine_mammal_activity`
- `water_clarity_observation`
- `surf_line_activity`
- `swimmer_density`
- `vessel_activity`
- `other`

The Drone Operator Console presents uppercase UI labels and maps them to this API enum. `POOR_VISIBILITY` maps to `water_clarity_observation`; `NO_SIGHTING_PATROL` maps to `no_sighting_patrol_result`; `OTHER` maps to `other`.

### Console Field Mapping

Console required fields:

- `mission_id`
- `observation_type`
- `observed_at`
- `latitude`
- `longitude`
- `observer_role`
- `visual_confidence`
- `provenance`

| Console field | API field |
| --- | --- |
| `observed_at` | `timestamp` |
| `visual_confidence` | `confidence` |
| `species_guess` | `probable_species` |
| `estimated_size_m` | `estimated_length_m` |
| `estimated_count` | `count` |
| `provenance` | `source` |
| `observer_role` | `source_type` |
| `behavior_notes` | `observed_behavior` |
| `operator_notes` | `internal_notes` |
| `public_summary`, `visibility_notes`, `surf_zone_notes` | public-safe analyst note text |

Expected console provenance values:

- `drone_operator_visual`
- `lifeguard_visual`
- `analyst_reviewed_visual`
- `official_agency_report`
- `project_owner_analyst_visual_assessment`
- `demo_fixture`

Validation bounds:

- latitude: `-90` to `90`
- longitude: `-180` to `180`
- count: `1` to `1000`, except `no_sighting_patrol_result` may use `0`
- estimated length: `0.1` to `20` meters when present
- confidence/species confidence: `0` to `1`
- timestamp is required and must parse as a date/time
- observation type, review status, and species assessment source must use known enumerations

Species guesses remain provisional operator metadata unless confirmed by an official source or qualified review. `official_species_classification` remains separate from operator guess fields.

## Map-Ready Feed Fields

Each feed item includes latitude, longitude, timestamp, observation type, review status, confidence, mission ID, source type, active pack, explanation summary, recommended action, recommended surveillance pattern, expiration, and data freshness.
