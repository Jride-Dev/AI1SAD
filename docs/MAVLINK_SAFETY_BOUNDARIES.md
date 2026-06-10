# MAVLink Safety Boundaries

Phase 25B is read-only telemetry ingestion.

AI1SAD must not:

- arm or disarm aircraft
- take off or land
- upload, change, or execute waypoints
- change flight modes
- use offboard control
- transmit MAVLink command messages
- add DJI-specific dependencies
- infer sightings from telemetry alone
- add computer-vision inference

## Bridge Behavior

- Disabled by default with `MAVLINK_BRIDGE_ENABLED=false`
- UDP listen mode disabled by default with `MAVLINK_UDP_LISTEN_ENABLED=false`
- Posts only normalized telemetry to the existing AI1SAD drone telemetry endpoint
- Adds no command endpoints
- Adds no aircraft-control APIs
- Adds no broad scoring weights

Telemetry is context for mission tracks and operational review. It is not animal detection, species classification, or warning evidence by itself.

