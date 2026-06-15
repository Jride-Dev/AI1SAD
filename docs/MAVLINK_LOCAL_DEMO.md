# MAVLink Local Demo

The local demo replays a safe Panama City shoreline patrol telemetry fixture into the existing drone telemetry endpoint.

## Prerequisites

Run the AI1SAD backend with drone ingestion enabled:

```powershell
$env:DRONE_INGEST_ENABLED="true"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Enable the bridge only for the local demo shell:

```powershell
$env:MAVLINK_BRIDGE_ENABLED="true"
$env:AI1SAD_BASE_URL="http://localhost:8000"
$env:MISSION_ID="mission-panama-city-mavlink-demo"
$env:DRONE_ID="drone-panama-city-mavlink-demo"
```

## Run The Demo

```powershell
python scripts/demo_drone_telemetry_bridge.py
```

The script:

1. creates or reuses a local demo mission
2. replays `tests/fixtures/mavlink/panama_city_demo_telemetry.jsonl`
3. posts normalized telemetry records to `/api/v1/drone/missions/{mission_id}/telemetry`
4. fetches mission detail
5. fetches the public surveillance feed
6. prints concise pass/fail output

After the backend and frontend are running, the Drone Operator Console can be opened at:

```text
http://localhost:5174/drone-console
```

Use the console to review the demo mission ID and submit human-entered observations. The console does not read `.tlog` files, listen to UDP, or send MAVLink commands.

## Generic Fixture Replay

```powershell
python scripts/run_mavlink_bridge.py --fixture-jsonl tests/fixtures/mavlink/panama_city_demo_telemetry.jsonl
```

`.tlog` and UDP modes are placeholders in Phase 25B and do not parse or transmit MAVLink traffic yet.
