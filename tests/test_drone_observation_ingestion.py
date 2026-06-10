from __future__ import annotations

import json
import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.config import get_settings
from app.mongodb import get_database
from app.services.drone_observations import map_feed_item
from tests.test_public_api_privacy import FakeDB


class DroneObservationIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["DRONE_INGEST_ENABLED"] = "true"
        get_settings.cache_clear()
        self.db = FakeDB()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_database] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        os.environ.pop("DRONE_INGEST_ENABLED", None)
        get_settings.cache_clear()

    def _mission_payload(self) -> dict:
        return {
            "mission_id": "mission-test-drone",
            "drone_id": "drone-1",
            "operator_id": "operator-1",
            "operator_role": "human_pilot",
            "region": "Florida",
            "pack_id": "florida",
            "mission_type": "shoreline_parallel_sweep",
            "started_at": "2099-06-08T17:00:00Z",
            "launch_location": {"latitude": 30.1826, "longitude": -85.7539},
            "recommended_pattern": "post_sighting_focus_area",
            "visibility": "public",
            "notes_internal": "private mission notes",
        }

    def _create_mission(self) -> None:
        response = self.client.post("/api/v1/drone/missions", json=self._mission_payload())
        self.assertEqual(response.status_code, 200)

    def test_drone_mission_creation_is_human_approved_without_flight_control(self):
        response = self.client.post("/api/v1/drone/missions", json=self._mission_payload())
        self.assertEqual(response.status_code, 200)
        mission = response.json()["mission"]
        self.assertTrue(mission["human_approved"])
        self.assertFalse(mission["autonomous_flight_control"])
        self.assertFalse(response.json()["flight_control_commands_exposed"])
        self.assertNotIn("operator_id", mission)
        self.assertNotIn("notes_internal", mission)

    def test_drone_write_endpoints_are_disabled_by_default(self):
        os.environ.pop("DRONE_INGEST_ENABLED", None)
        get_settings.cache_clear()
        response = self.client.post("/api/v1/drone/missions", json=self._mission_payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Drone ingestion endpoint is disabled")
        os.environ["DRONE_INGEST_ENABLED"] = "true"
        get_settings.cache_clear()

    def test_telemetry_ingestion(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/telemetry",
            json={
                "timestamp": "2099-06-08T17:05:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "altitude_m": 35,
                "gps_fix_quality": "good",
            },
        )
        self.assertEqual(response.status_code, 200)
        telemetry = response.json()["telemetry"]
        self.assertEqual(telemetry["mission_id"], "mission-test-drone")
        self.assertFalse(response.json()["flight_control_commands_exposed"])

    def test_telemetry_validation_bounds(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/telemetry",
            json={
                "timestamp": "2099-06-08T17:05:00Z",
                "latitude": 95,
                "longitude": -85.7539,
                "altitude_m": 35,
                "battery_percent": 50,
            },
        )
        self.assertEqual(response.status_code, 422)

        missing_timestamp = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/telemetry",
            json={"latitude": 30.1826, "longitude": -85.7539},
        )
        self.assertEqual(missing_timestamp.status_code, 422)

    def test_observation_ingestion_filters_private_notes(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "observation_id": "observation-1",
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "probable_species": "bull shark",
                "species_assessment_source": "analyst_visual_assessment",
                "species_confidence": 0.62,
                "analyst_notes": "private analyst note",
                "internal_notes": "private internal note",
                "confidence": 0.68,
                "review_status": "analyst_reviewed",
            },
        )
        self.assertEqual(response.status_code, 200)
        text = json.dumps(response.json())
        self.assertNotIn("private analyst note", text)
        self.assertNotIn("private internal note", text)
        listed = self.client.get("/api/v1/drone/missions/mission-test-drone/observations")
        self.assertEqual(listed.status_code, 200)
        self.assertNotIn("private", json.dumps(listed.json()).lower())

    def test_observation_validation_bounds_and_choices(self):
        self._create_mission()
        invalid_type = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "waypoint_command",
                "review_status": "unreviewed",
            },
        )
        self.assertEqual(invalid_type.status_code, 422)
        invalid_length = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "review_status": "unreviewed",
                "estimated_length_m": 55,
            },
        )
        self.assertEqual(invalid_length.status_code, 422)

    def test_unreviewed_vs_reviewed_sighting_behavior(self):
        self._create_mission()
        unreviewed = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.45,
                "review_status": "unreviewed",
            },
        )
        self.assertEqual(unreviewed.status_code, 200)
        unreviewed_score = self.client.get("/api/v1/drone/surveillance-feed").json()["surveillance"]["zones"][0]["surveillance_priority_score"]
        reviewed = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:09:00Z",
                "latitude": 30.1827,
                "longitude": -85.754,
                "observation_type": "shark_sighting",
                "confidence": 0.75,
                "review_status": "analyst_reviewed",
            },
        )
        self.assertEqual(reviewed.status_code, 200)
        reviewed_score = self.client.get("/api/v1/drone/surveillance-feed").json()["surveillance"]["zones"][0]["surveillance_priority_score"]
        self.assertGreater(reviewed_score, unreviewed_score)

    def test_sighting_cluster_alert_and_map_ready_feed(self):
        self._create_mission()
        for index in range(2):
            response = self.client.post(
                "/api/v1/drone/missions/mission-test-drone/observations",
                json={
                    "timestamp": f"2099-06-08T17:1{index}:00Z",
                    "latitude": 30.1826 + index * 0.001,
                    "longitude": -85.7539,
                    "observation_type": "shark_sighting",
                    "confidence": 0.8,
                    "review_status": "confirmed",
                },
            )
            self.assertEqual(response.status_code, 200)
        feed = self.client.get("/api/v1/drone/surveillance-feed").json()
        first = feed["results"][0]
        for key in ["latitude", "longitude", "timestamp", "observation_type", "review_status", "confidence", "mission_id", "source_type", "active_pack", "explanation_summary", "recommended_action", "recommended_surveillance_pattern", "expires_at", "data_freshness"]:
            self.assertIn(key, first)
        self.assertTrue(any(alert["alert_type"] == "sighting_cluster" for alert in feed["alerts"]))

    def test_no_sighting_result_does_not_imply_safety(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:20:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "no_sighting_patrol_result",
                "count": 0,
                "confidence": 0.55,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(response.status_code, 200)
        feed_item = map_feed_item(response.json()["observation"])
        self.assertIn("not treat no-sighting patrol as proof of safety", feed_item["recommended_action"])

    def test_mission_completion(self):
        self._create_mission()
        response = self.client.post("/api/v1/drone/missions/mission-test-drone/complete", json={"ended_at": "2099-06-08T18:00:00Z"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mission"]["status"], "completed")


