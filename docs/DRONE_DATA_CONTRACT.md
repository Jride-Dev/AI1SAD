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
- `media_reference_type` (enum: `local_filename`, `drone_clip_id`, `camera_card_reference`, `external_url`, `agency_evidence_id`, `private_case_reference`, `none`)
- `media_timestamp`
- `analyst_review_status` (enum: `unreviewed`, `needs_review`, `in_review`, `reviewed`, `rejected`, `inconclusive`)
- `analyst_reviewed_at`
- `analyst_reviewer_role`
- `analyst_notes_private`
- `public_review_summary`
- `review_outcome` (enum: `no_public_change`, `confirms_operator_observation`, `downgrades_operator_observation`, `upgrades_operator_observation`, `species_uncertain`, `false_positive`, `duplicate`, `unusable_media`)
- `evidence_confidence`
- `confidence`
- `review_status`
- `source`
- `source_type`
- `public_visibility`

Private analyst or internal notes, analyst private notes, analyst reviewer role, analyst review timestamps, raw media references, media reference types, and media timestamps are never exposed through public endpoints. Media-reference visibility is private-by-default until a future phase defines public-safe attachment release rules.

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
- confidence/species confidence/evidence confidence: `0` to `1`; impossible values are rejected rather than clamped
- timestamp is required and must parse as a date/time
- observation type, review status, and species assessment source must use known enumerations

Species guesses remain provisional operator metadata unless confirmed by an official source or qualified review. `official_species_classification` remains separate from operator guess fields.

### Analyst Review Fields

Phase 25D-A adds metadata-only analyst review fields. These are annotations on existing observations:

- `analyst_review_status`, `review_outcome`, `public_review_summary`, `evidence_confidence` are review metadata
- `analyst_notes_private`, `analyst_reviewer_role`, `analyst_reviewed_at`, `media_reference`, `media_reference_type`, and `media_timestamp` are private and excluded from public responses
- `media_reference_type` and `media_timestamp` describe the associated media internally (reference only; no upload or hosting)
- The PATCH endpoint updates analyst review fields on an existing observation without modifying the original

See [Observation Analyst Review](OBSERVATION_ANALYST_REVIEW.md).

### Future Attachment Fields (Design Reference Only)

Phase 25D-B documents a future attachment model for media evidence. The proposed fields are design-only and not implemented. See [Media Attachment Storage Design](MEDIA_ATTACHMENT_STORAGE_DESIGN.md) for the full proposal.

Future fields under review include: `attachment_id`, `observation_id`, `mission_id`, `storage_backend`, `storage_key`, `original_filename`, `media_kind`, `mime_type`, `file_size_bytes`, `captured_at`, `uploaded_at`, `uploaded_by_role`, `review_visibility`, `public_release_status`, `retention_policy`, `checksum_sha256`, `redaction_status`, `chain_of_custody_note`, `evidence_confidence`, `analyst_review_status`, and `public_summary`.

No storage implementation is included in Phase 25D-B.

## Map-Ready Feed Fields

Each feed item includes latitude, longitude, timestamp, observation type, review status, confidence, mission ID, source type, active pack, explanation summary, recommended action, recommended surveillance pattern, expiration, and data freshness.
