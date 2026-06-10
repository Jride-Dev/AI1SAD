from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib import error, request


MAX_BATCH_SIZE = 100
DEFAULT_BATCH_SIZE = 25
DEFAULT_FLUSH_INTERVAL_SECONDS = 2.0
SOURCE_TYPES = {"fixture_replay", "tlog_replay", "udp_live"}


class MavlinkBridgeError(ValueError):
    """Raised when read-only MAVLink telemetry bridge input is invalid."""


@dataclass(frozen=True)
class MavlinkBridgeConfig:
    enabled: bool = False
    connection: str | None = None
    ai1sad_base_url: str = "http://localhost:8000"
    drone_api_key: str | None = None
    mission_id: str = "mission-mavlink-demo"
    drone_id: str = "drone-mavlink-demo"
    batch_size: int = DEFAULT_BATCH_SIZE
    flush_interval_seconds: float = DEFAULT_FLUSH_INTERVAL_SECONDS
    source_type: str = "fixture_replay"
    udp_listen_enabled: bool = False

    @classmethod
    def from_env(cls) -> "MavlinkBridgeConfig":
        return cls(
            enabled=os.getenv("MAVLINK_BRIDGE_ENABLED", "false").lower() == "true",
            connection=os.getenv("MAVLINK_CONNECTION") or None,
            ai1sad_base_url=os.getenv("AI1SAD_BASE_URL", "http://localhost:8000").rstrip("/"),
            drone_api_key=os.getenv("AI1SAD_DRONE_API_KEY") or None,
            mission_id=os.getenv("MISSION_ID", "mission-mavlink-demo"),
            drone_id=os.getenv("DRONE_ID", "drone-mavlink-demo"),
            batch_size=parse_batch_size(os.getenv("BATCH_SIZE", str(DEFAULT_BATCH_SIZE))),
            flush_interval_seconds=float(os.getenv("FLUSH_INTERVAL_SECONDS", str(DEFAULT_FLUSH_INTERVAL_SECONDS))),
            source_type=os.getenv("SOURCE_TYPE", "fixture_replay"),
            udp_listen_enabled=os.getenv("MAVLINK_UDP_LISTEN_ENABLED", "false").lower() == "true",
        )


Transport = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


def parse_batch_size(value: Any) -> int:
    size = int(value)
    if size < 1 or size > MAX_BATCH_SIZE:
        raise MavlinkBridgeError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    return size


def parse_timestamp(value: Any) -> str:
    if value in {None, ""}:
        raise MavlinkBridgeError("timestamp is required")
    if isinstance(value, datetime):
        parsed = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    text = str(value)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def bounded_float(value: Any, field: str, minimum: float, maximum: float) -> float:
    if value in {None, ""}:
        raise MavlinkBridgeError(f"{field} is required")
    result = float(value)
    if result < minimum or result > maximum:
        raise MavlinkBridgeError(f"{field} must be between {minimum} and {maximum}")
    return result


def optional_bounded_float(value: Any, field: str, minimum: float, maximum: float) -> float | None:
    if value in {None, ""}:
        return None
    return bounded_float(value, field, minimum, maximum)


def first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def normalize_coordinate(value: Any, field: str) -> float:
    result = float(value)
    if abs(result) > 180 and float(result).is_integer():
        result = result / 10_000_000
    if field == "latitude":
        if result < -90 or result > 90:
            raise MavlinkBridgeError("latitude must be between -90 and 90")
    elif result < -180 or result > 180:
        raise MavlinkBridgeError("longitude must be between -180 and 180")
    return result


def normalize_mavlink_telemetry(record: dict[str, Any], *, mission_id: str, drone_id: str, source_type: str) -> dict[str, Any]:
    if source_type not in SOURCE_TYPES:
        raise MavlinkBridgeError(f"source_type must be one of: {', '.join(sorted(SOURCE_TYPES))}")
    if not isinstance(record, dict):
        raise MavlinkBridgeError("telemetry record must be an object")
    timestamp = parse_timestamp(first_present(record, "timestamp", "time", "time_boot_ms"))
    lat_value = first_present(record, "latitude", "lat")
    lon_value = first_present(record, "longitude", "lon", "lng")
    if lat_value is None or lon_value is None:
        raise MavlinkBridgeError("latitude and longitude are required")
    normalized = {
        "mission_id": mission_id,
        "drone_id": drone_id,
        "timestamp": timestamp,
        "latitude": normalize_coordinate(lat_value, "latitude"),
        "longitude": normalize_coordinate(lon_value, "longitude"),
        "altitude_m": optional_bounded_float(first_present(record, "altitude_m", "relative_alt_m", "alt"), "altitude_m", -20, 1000),
        "heading_deg": optional_bounded_float(first_present(record, "heading_deg", "hdg", "yaw_deg"), "heading_deg", 0, 360),
        "groundspeed_mps": optional_bounded_float(first_present(record, "groundspeed_mps", "groundspeed", "vx_mps"), "groundspeed_mps", 0, 80),
        "battery_percent": optional_bounded_float(first_present(record, "battery_percent", "battery_remaining"), "battery_percent", 0, 100),
        "gps_fix_quality": str(first_present(record, "gps_fix_quality", "fix_type") or "unknown")[:40],
        "camera_heading_deg": optional_bounded_float(first_present(record, "camera_heading_deg", "gimbal_yaw_deg"), "camera_heading_deg", 0, 360),
        "camera_pitch_deg": optional_bounded_float(first_present(record, "camera_pitch_deg", "gimbal_pitch_deg"), "camera_pitch_deg", -180, 180),
        "source": "mavlink_bridge",
        "source_type": source_type,
        "public_visibility": True,
    }
    return normalized


def iter_jsonl_fixture(path: str | Path) -> Iterable[dict[str, Any]]:
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            try:
                yield json.loads(text)
            except json.JSONDecodeError as exc:
                raise MavlinkBridgeError(f"Invalid JSONL at line {line_number}: {exc.msg}") from exc


def iter_tlog_replay(_path: str | Path) -> Iterable[dict[str, Any]]:
    raise MavlinkBridgeError("Local .tlog replay requires a future reviewed parser; no MAVLink dependency is loaded in Phase 25B.")


def iter_udp_live(_connection: str | None, *, enabled: bool) -> Iterable[dict[str, Any]]:
    if not enabled:
        raise MavlinkBridgeError("UDP listen mode is disabled by default. Set MAVLINK_UDP_LISTEN_ENABLED=true for reviewed local tests.")
    raise MavlinkBridgeError("UDP listen mode is reserved for a future read-only parser and sends no MAVLink messages in Phase 25B.")


def batches(records: Iterable[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    batch_size = parse_batch_size(size)
    current: list[dict[str, Any]] = []
    for record in records:
        current.append(record)
        if len(current) >= batch_size:
            yield current
            current = []
    if current:
        yield current


def default_transport(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MavlinkBridgeError(f"AI1SAD telemetry POST failed with HTTP {exc.code}: {detail}") from exc


def submit_telemetry_batch(
    records: list[dict[str, Any]],
    *,
    config: MavlinkBridgeConfig,
    transport: Transport = default_transport,
) -> dict[str, Any]:
    if not config.enabled:
        raise MavlinkBridgeError("MAVLink bridge is disabled. Set MAVLINK_BRIDGE_ENABLED=true to run read-only telemetry ingestion.")
    parse_batch_size(len(records))
    url = f"{config.ai1sad_base_url}/api/v1/drone/missions/{config.mission_id}/telemetry"
    headers = {"User-Agent": "ai1sad-mavlink-readonly-bridge/1.0"}
    if config.drone_api_key:
        headers["x-api-key"] = config.drone_api_key
    submitted = 0
    for record in records:
        payload = normalize_mavlink_telemetry(record, mission_id=config.mission_id, drone_id=config.drone_id, source_type=config.source_type)
        transport(url, payload, headers)
        submitted += 1
    return {"submitted": submitted, "mission_id": config.mission_id, "source_type": config.source_type}


def replay_jsonl_fixture(path: str | Path, *, config: MavlinkBridgeConfig, transport: Transport = default_transport) -> dict[str, Any]:
    total = 0
    for batch in batches(iter_jsonl_fixture(path), config.batch_size):
        result = submit_telemetry_batch(batch, config=config, transport=transport)
        total += int(result["submitted"])
        if config.flush_interval_seconds > 0:
            time.sleep(min(config.flush_interval_seconds, 5.0))
    return {"submitted": total, "mission_id": config.mission_id, "source_type": config.source_type}

