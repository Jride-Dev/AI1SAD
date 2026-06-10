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
- `public_visibility`

Private analyst or internal notes are never exposed through public endpoints.

Validation bounds:

- latitude: `-90` to `90`
- longitude: `-180` to `180`
- count: `1` to `1000`, except `no_sighting_patrol_result` may use `0`
- estimated length: `0.1` to `20` meters when present
- confidence/species confidence: `0` to `1`
- timestamp is required and must parse as a date/time
- observation type, review status, and species assessment source must use known enumerations

## Map-Ready Feed Fields

Each feed item includes latitude, longitude, timestamp, observation type, review status, confidence, mission ID, source type, active pack, explanation summary, recommended action, recommended surveillance pattern, expiration, and data freshness.
