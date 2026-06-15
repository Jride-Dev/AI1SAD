# MAVLink Telemetry Bridge

Phase 25B adds a read-only telemetry bridge that normalizes replayed or future live MAVLink-style telemetry into the existing AI1SAD drone telemetry ingestion endpoint.

This bridge does not control aircraft.

## Supported Modes

- deterministic JSONL fixture replay
- local `.tlog` replay placeholder, guarded until a reviewed parser is added
- optional UDP listen placeholder, disabled by default

No MAVLink dependency is loaded in this phase. The bridge uses standard Python libraries and normalizes telemetry-shaped records only.

## Configuration

```text
MAVLINK_BRIDGE_ENABLED=false
MAVLINK_CONNECTION=
AI1SAD_BASE_URL=http://localhost:8000
AI1SAD_DRONE_API_KEY=
MISSION_ID=mission-mavlink-demo
DRONE_ID=drone-mavlink-demo
BATCH_SIZE=25
FLUSH_INTERVAL_SECONDS=2
SOURCE_TYPE=fixture_replay
MAVLINK_UDP_LISTEN_ENABLED=false
```

The bridge is disabled unless `MAVLINK_BRIDGE_ENABLED=true`.

The AI1SAD backend must also allow drone writes with `DRONE_INGEST_ENABLED=true`.

## Normalized Telemetry Fields

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
- `source: mavlink_bridge`
- `source_type: fixture_replay | tlog_replay | udp_live`

Unavailable values remain `null`. The bridge does not invent telemetry.

## Validation

- latitude: `-90` to `90`
- longitude: `-180` to `180`
- altitude: `-20` to `1000` meters
- heading/camera heading: `0` to `360`
- camera pitch: `-180` to `180`
- battery: `0` to `100`
- batch size: `1` to `100`
- timestamp is required and parseable

Telemetry alone never creates a shark sighting or species observation.

## Operator Console Relationship

The Phase 25C Drone Operator Console can display mission context that was populated by the read-only bridge when such telemetry is available through existing mission/feed workflows.

The console does not connect to MAVLink, does not transmit MAVLink messages, and does not create sightings from telemetry alone. Human-entered observations remain separate from telemetry records.
