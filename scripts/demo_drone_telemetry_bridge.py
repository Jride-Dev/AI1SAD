from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, request

from app.integrations.mavlink_bridge import MavlinkBridgeConfig, MavlinkBridgeError, replay_jsonl_fixture


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "mavlink" / "panama_city_demo_telemetry.jsonl"


def api_json(method: str, url: str, payload: dict | None = None, api_key: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json", "User-Agent": "ai1sad-mavlink-demo/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"detail": body}
        return exc.code, parsed


def create_or_reuse_mission(config: MavlinkBridgeConfig) -> None:
    base = config.ai1sad_base_url.rstrip("/")
    mission_url = f"{base}/api/v1/drone/missions/{config.mission_id}"
    status, _payload = api_json("GET", mission_url, api_key=config.drone_api_key)
    if status == 200:
        print("PASS: demo mission already exists")
        return
    create_payload = {
        "mission_id": config.mission_id,
        "drone_id": config.drone_id,
        "operator_id": "local-demo-operator",
        "operator_role": "human_operator",
        "region": "Florida",
        "pack_id": "florida",
        "mission_type": "shoreline_parallel_sweep",
        "started_at": "2026-06-08T17:00:00Z",
        "launch_location": {"latitude": 30.1826, "longitude": -85.7539},
        "recommended_pattern": "shoreline_parallel_sweep",
        "visibility": "public",
        "notes_public": "Local read-only MAVLink telemetry bridge demo mission.",
    }
    status, payload = api_json("POST", f"{base}/api/v1/drone/missions", create_payload, api_key=config.drone_api_key)
    if status != 200:
        raise MavlinkBridgeError(f"demo mission create failed: HTTP {status} {payload}")
    print("PASS: demo mission created")


def main() -> int:
    config = MavlinkBridgeConfig.from_env()
    config = MavlinkBridgeConfig(
        enabled=config.enabled,
        connection=config.connection,
        ai1sad_base_url=config.ai1sad_base_url,
        drone_api_key=config.drone_api_key,
        mission_id=os.getenv("MISSION_ID", "mission-panama-city-mavlink-demo"),
        drone_id=os.getenv("DRONE_ID", "drone-panama-city-mavlink-demo"),
        batch_size=config.batch_size,
        flush_interval_seconds=0,
        source_type="fixture_replay",
        udp_listen_enabled=config.udp_listen_enabled,
    )
    try:
        create_or_reuse_mission(config)
        result = replay_jsonl_fixture(FIXTURE, config=config)
        print(f"PASS: replayed telemetry records={result['submitted']}")
        base = config.ai1sad_base_url.rstrip("/")
        mission_status, _mission = api_json("GET", f"{base}/api/v1/drone/missions/{config.mission_id}", api_key=config.drone_api_key)
        feed_status, feed = api_json("GET", f"{base}/api/v1/drone/surveillance-feed", api_key=config.drone_api_key)
        if mission_status != 200:
            raise MavlinkBridgeError(f"mission detail failed: HTTP {mission_status}")
        if feed_status != 200:
            raise MavlinkBridgeError(f"surveillance feed failed: HTTP {feed_status}")
        print(f"PASS: mission detail available and surveillance feed returned {len(feed.get('results', []))} items")
        return 0
    except MavlinkBridgeError as exc:
        print(f"FAIL: {exc}")
        print("Hint: backend must have DRONE_INGEST_ENABLED=true and bridge must have MAVLINK_BRIDGE_ENABLED=true.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

