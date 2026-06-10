from __future__ import annotations

import argparse
from pathlib import Path

from app.integrations.mavlink_bridge import (
    MavlinkBridgeConfig,
    MavlinkBridgeError,
    iter_tlog_replay,
    iter_udp_live,
    replay_jsonl_fixture,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only AI1SAD MAVLink telemetry bridge.")
    parser.add_argument("--fixture-jsonl", help="Replay deterministic JSONL telemetry fixture.")
    parser.add_argument("--tlog", help="Attempt local .tlog replay. Phase 25B keeps this parser disabled unless reviewed later.")
    parser.add_argument("--udp", action="store_true", help="Attempt UDP listen mode. Disabled by default and read-only.")
    args = parser.parse_args()

    config = MavlinkBridgeConfig.from_env()
    try:
        if args.fixture_jsonl:
            result = replay_jsonl_fixture(Path(args.fixture_jsonl), config=config)
        elif args.tlog:
            list(iter_tlog_replay(args.tlog))
            result = {"submitted": 0, "mode": "tlog_replay"}
        elif args.udp:
            list(iter_udp_live(config.connection, enabled=config.udp_listen_enabled))
            result = {"submitted": 0, "mode": "udp_live"}
        else:
            raise MavlinkBridgeError("Select --fixture-jsonl, --tlog, or --udp")
    except MavlinkBridgeError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: submitted={result.get('submitted', 0)} mission_id={result.get('mission_id', config.mission_id)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

