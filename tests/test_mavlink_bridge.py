from __future__ import annotations

import unittest
from pathlib import Path

from app.integrations import mavlink_bridge
from app.integrations.mavlink_bridge import (
    MAX_BATCH_SIZE,
    MavlinkBridgeConfig,
    MavlinkBridgeError,
    iter_jsonl_fixture,
    iter_udp_live,
    normalize_mavlink_telemetry,
    replay_jsonl_fixture,
    submit_telemetry_batch,
)


FIXTURE = Path(__file__).parent / "fixtures" / "mavlink" / "panama_city_demo_telemetry.jsonl"


class MavlinkBridgeTests(unittest.TestCase):
    def config(self, **overrides):
        values = {
            "enabled": True,
            "ai1sad_base_url": "http://ai1sad.test",
            "mission_id": "mission-panama-city-demo",
            "drone_id": "drone-panama-city-demo",
            "batch_size": 2,
            "flush_interval_seconds": 0,
            "source_type": "fixture_replay",
        }
        values.update(overrides)
        return MavlinkBridgeConfig(**values)

    def test_fixture_parsing(self):
        records = list(iter_jsonl_fixture(FIXTURE))
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]["gps_fix_quality"], "3d")

    def test_telemetry_normalization(self):
        record = next(iter_jsonl_fixture(FIXTURE))
        telemetry = normalize_mavlink_telemetry(record, mission_id="mission-1", drone_id="drone-1", source_type="fixture_replay")
        self.assertEqual(telemetry["mission_id"], "mission-1")
        self.assertEqual(telemetry["drone_id"], "drone-1")
        self.assertEqual(telemetry["source"], "mavlink_bridge")
        self.assertEqual(telemetry["source_type"], "fixture_replay")
        self.assertEqual(telemetry["latitude"], 30.1826)
        self.assertEqual(telemetry["longitude"], -85.7539)

    def test_invalid_coordinate_rejection(self):
        with self.assertRaisesRegex(MavlinkBridgeError, "latitude"):
            normalize_mavlink_telemetry(
                {"timestamp": "2026-06-08T17:01:00Z", "latitude": 91, "longitude": -85.7},
                mission_id="mission-1",
                drone_id="drone-1",
                source_type="fixture_replay",
            )

    def test_invalid_battery_rejection(self):
        with self.assertRaisesRegex(MavlinkBridgeError, "battery_percent"):
            normalize_mavlink_telemetry(
                {"timestamp": "2026-06-08T17:01:00Z", "latitude": 30.1, "longitude": -85.7, "battery_percent": 101},
                mission_id="mission-1",
                drone_id="drone-1",
                source_type="fixture_replay",
            )

    def test_missing_required_field_rejection(self):
        with self.assertRaisesRegex(MavlinkBridgeError, "timestamp"):
            normalize_mavlink_telemetry(
                {"latitude": 30.1, "longitude": -85.7},
                mission_id="mission-1",
                drone_id="drone-1",
                source_type="fixture_replay",
            )

    def test_bounded_batch_size(self):
        records = [
            {"timestamp": "2026-06-08T17:01:00Z", "latitude": 30.1, "longitude": -85.7}
            for _ in range(MAX_BATCH_SIZE + 1)
        ]
        with self.assertRaisesRegex(MavlinkBridgeError, "batch_size"):
            submit_telemetry_batch(records, config=self.config())

    def test_bridge_disabled_by_default(self):
        with self.assertRaisesRegex(MavlinkBridgeError, "disabled"):
            submit_telemetry_batch(
                [{"timestamp": "2026-06-08T17:01:00Z", "latitude": 30.1, "longitude": -85.7}],
                config=MavlinkBridgeConfig(),
            )

    def test_udp_disabled_unless_explicitly_enabled(self):
        with self.assertRaisesRegex(MavlinkBridgeError, "UDP listen mode is disabled"):
            list(iter_udp_live("udp:127.0.0.1:14550", enabled=False))

    def test_no_flight_control_imports_or_outbound_mavlink_commands(self):
        source = Path(mavlink_bridge.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("pymavlink", source)
        self.assertNotIn("mavutil", source)
        self.assertNotIn("command_long_send", source)
        self.assertNotIn("set_mode_send", source)
        self.assertNotIn("mission_item", source)
        self.assertNotIn("waypoint", source)
        self.assertNotIn("arm_disarm", source)
        self.assertNotIn("takeoff", source)

    def test_no_shark_sighting_created_from_telemetry_alone(self):
        record = next(iter_jsonl_fixture(FIXTURE))
        telemetry = normalize_mavlink_telemetry(record, mission_id="mission-1", drone_id="drone-1", source_type="fixture_replay")
        self.assertNotIn("observation_type", telemetry)
        self.assertNotIn("probable_species", telemetry)
        self.assertEqual(telemetry["source"], "mavlink_bridge")

    def test_mocked_api_submission_succeeds(self):
        calls = []

        def transport(url, payload, headers):
            calls.append((url, payload, headers))
            return {"status": "created"}

        result = replay_jsonl_fixture(FIXTURE, config=self.config(), transport=transport)
        self.assertEqual(result["submitted"], 5)
        self.assertEqual(len(calls), 5)
        self.assertTrue(calls[0][0].endswith("/api/v1/drone/missions/mission-panama-city-demo/telemetry"))
        self.assertEqual(calls[0][1]["source_type"], "fixture_replay")


if __name__ == "__main__":
    unittest.main()

