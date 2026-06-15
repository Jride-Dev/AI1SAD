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
        os.environ.pop("MEDIA_ATTACHMENTS_ENABLED", None)
        os.environ.pop("MEDIA_ATTACHMENTS_STORAGE_ROOT", None)
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

    def _create_observation(self, observation_type: str = "shark_sighting") -> str:
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": observation_type,
                "confidence": 0.55,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["observation"]["observation_id"]

    def _enable_media_attachments(self) -> None:
        os.environ["MEDIA_ATTACHMENTS_ENABLED"] = "true"
        os.environ["MEDIA_ATTACHMENTS_STORAGE_ROOT"] = "./data/media_attachments"
        get_settings.cache_clear()

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

    def test_other_observation_type_is_accepted_for_operator_console(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "other",
                "confidence": 0.5,
                "review_status": "operator_reviewed",
                "source": "drone_operator_visual",
                "source_type": "drone_operator",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["observation"]["observation_type"], "other")

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

    def test_analyst_review_fields_accepted_on_observation_creation(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.6,
                "review_status": "operator_reviewed",
                "media_reference": "clip-001",
                "media_reference_type": "drone_clip_id",
                "analyst_review_status": "needs_review",
                "review_outcome": "confirms_operator_observation",
                "analyst_notes_private": "Analyst private note",
                "public_review_summary": "Operator observation consistent with clip review",
                "evidence_confidence": 0.72,
            },
        )
        self.assertEqual(response.status_code, 200)
        obs = response.json()["observation"]
        self.assertNotIn("media_reference", obs)
        self.assertNotIn("media_reference_type", obs)
        self.assertNotIn("media_timestamp", obs)
        self.assertEqual(obs.get("analyst_review_status"), "needs_review")
        self.assertEqual(obs.get("review_outcome"), "confirms_operator_observation")
        self.assertNotIn("analyst_notes_private", obs)
        self.assertEqual(obs.get("public_review_summary"), "Operator observation consistent with clip review")
        self.assertEqual(obs.get("evidence_confidence"), 0.72)

    def test_private_media_reference_types_excluded_from_public_output(self):
        self._create_mission()
        for media_type in ["local_filename", "private_case_reference"]:
            reference = f"sensitive-{media_type}-001"
            response = self.client.post(
                "/api/v1/drone/missions/mission-test-drone/observations",
                json={
                    "timestamp": "2099-06-08T17:08:00Z",
                    "latitude": 30.1826,
                    "longitude": -85.7539,
                    "observation_type": "shark_sighting",
                    "confidence": 0.6,
                    "review_status": "operator_reviewed",
                    "media_reference": reference,
                    "media_reference_type": media_type,
                    "media_timestamp": "2099-06-08T17:07:00Z",
                },
            )
            self.assertEqual(response.status_code, 200)
            created = json.dumps(response.json())
            self.assertNotIn(reference, created)
            self.assertNotIn("media_reference", created)
            self.assertNotIn("media_reference_type", created)
            self.assertNotIn("media_timestamp", created)

        listed = self.client.get("/api/v1/drone/missions/mission-test-drone/observations")
        self.assertEqual(listed.status_code, 200)
        listed_text = json.dumps(listed.json())
        self.assertNotIn("sensitive-local_filename-001", listed_text)
        self.assertNotIn("sensitive-private_case_reference-001", listed_text)
        self.assertNotIn("media_reference", listed_text)
        self.assertNotIn("media_reference_type", listed_text)
        self.assertNotIn("media_timestamp", listed_text)

    def test_unsupported_media_reference_type_is_rejected(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "review_status": "operator_reviewed",
                "media_reference_type": "youtube_video",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_unsupported_analyst_review_status_is_rejected(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "review_status": "operator_reviewed",
                "analyst_review_status": "auto_approved",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_unsupported_review_outcome_is_rejected(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "review_status": "operator_reviewed",
                "review_outcome": "autonomous_detection",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_observation_confidence_rejects_impossible_values(self):
        self._create_mission()
        for field, value in [("confidence", 1.7), ("confidence", -0.1), ("evidence_confidence", 1.2), ("evidence_confidence", -0.2)]:
            response = self.client.post(
                "/api/v1/drone/missions/mission-test-drone/observations",
                json={
                    "timestamp": "2099-06-08T17:08:00Z",
                    "latitude": 30.1826,
                    "longitude": -85.7539,
                    "observation_type": "shark_sighting",
                    "review_status": "operator_reviewed",
                    field: value,
                },
            )
            self.assertEqual(response.status_code, 422, field)

    def test_observation_confidence_boundaries_are_accepted(self):
        self._create_mission()
        for value in [0, 1]:
            response = self.client.post(
                "/api/v1/drone/missions/mission-test-drone/observations",
                json={
                    "timestamp": "2099-06-08T17:08:00Z",
                    "latitude": 30.1826,
                    "longitude": -85.7539,
                    "observation_type": "shark_sighting",
                    "review_status": "operator_reviewed",
                    "confidence": value,
                    "evidence_confidence": value,
                },
            )
            self.assertEqual(response.status_code, 200)
            observation = response.json()["observation"]
            self.assertEqual(observation["confidence"], value)
            self.assertEqual(observation["evidence_confidence"], value)

    def test_analyst_notes_private_excluded_from_public_feed(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.5,
                "review_status": "operator_reviewed",
                "analyst_notes_private": "Must not appear in public feed",
                "public_review_summary": "Safe summary text",
            },
        )
        self.assertEqual(response.status_code, 200)
        text = str(response.json())
        self.assertNotIn("Must not appear in public feed", text)
        self.assertIn("Safe summary text", text)

    def test_media_reference_does_not_create_sighting_alone(self):
        self._create_mission()
        response = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "water_clarity_observation",
                "media_reference": "clip-002",
                "confidence": 0.4,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(response.status_code, 200)
        feed = self.client.get("/api/v1/drone/surveillance-feed").json()
        matching = [item for item in feed["results"] if item.get("observation_type") == "water_clarity_observation"]
        self.assertGreater(len(matching), 0)
        for item in matching:
            self.assertNotEqual(item["explanation_summary"], "shark_sighting")
            self.assertNotIn("clip-002", str(item))

    def test_patch_observation_review_updates_fields(self):
        self._create_mission()
        created = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.55,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(created.status_code, 200)
        obs_id = created.json()["observation"]["observation_id"]
        patch = self.client.patch(
            f"/api/v1/drone/missions/mission-test-drone/observations/{obs_id}",
            json={
                "analyst_review_status": "in_review",
                "review_outcome": "species_uncertain",
                "public_review_summary": "Species unclear from available reference",
            },
        )
        self.assertEqual(patch.status_code, 200)
        patched = patch.json()["observation"]
        self.assertEqual(patched.get("analyst_review_status"), "in_review")
        self.assertEqual(patched.get("review_outcome"), "species_uncertain")
        self.assertEqual(patched.get("public_review_summary"), "Species unclear from available reference")

    def test_patch_observation_review_rejects_invalid_status(self):
        self._create_mission()
        created = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.55,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(created.status_code, 200)
        obs_id = created.json()["observation"]["observation_id"]
        patch = self.client.patch(
            f"/api/v1/drone/missions/mission-test-drone/observations/{obs_id}",
            json={"analyst_review_status": "auto_confirmed"},
        )
        self.assertEqual(patch.status_code, 422)

    def test_patch_observation_review_private_notes_filtered(self):
        self._create_mission()
        created = self.client.post(
            "/api/v1/drone/missions/mission-test-drone/observations",
            json={
                "timestamp": "2099-06-08T17:08:00Z",
                "latitude": 30.1826,
                "longitude": -85.7539,
                "observation_type": "shark_sighting",
                "confidence": 0.55,
                "review_status": "operator_reviewed",
            },
        )
        self.assertEqual(created.status_code, 200)
        obs_id = created.json()["observation"]["observation_id"]
        patch = self.client.patch(
            f"/api/v1/drone/missions/mission-test-drone/observations/{obs_id}",
            json={
                "analyst_review_status": "reviewed",
                "analyst_notes_private": "Highly sensitive private note",
            },
        )
        self.assertEqual(patch.status_code, 200)
        text = str(patch.json())
        self.assertNotIn("Highly sensitive private note", text)

    def test_attachment_writes_rejected_when_disabled(self):
        observation_id = self._create_observation()
        response = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Local media attachment prototype is disabled")

    def test_attachment_metadata_allowed_when_enabled_and_private_by_default(self):
        observation_id = self._create_observation()
        self._enable_media_attachments()
        response = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={
                "media_kind": "image",
                "media_reference_type": "local_filename",
                "original_filename": "frame-001.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 2048,
                "captured_at": "2099-06-08T17:07:30Z",
                "uploaded_by_role": "analyst",
                "review_visibility": "analyst_only",
                "public_summary": "Public-safe attachment summary",
                "evidence_confidence": 0.7,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        attachment = payload["attachment"]
        self.assertTrue(payload["private_by_default"])
        self.assertFalse(payload["public_feed_exposed"])
        self.assertFalse(payload["media_analysis_performed"])
        self.assertFalse(payload["sighting_created"])
        self.assertEqual(attachment["observation_id"], observation_id)
        self.assertEqual(attachment["mission_id"], "mission-test-drone")
        self.assertEqual(attachment["media_kind"], "image")
        self.assertEqual(attachment["review_visibility"], "analyst_only")
        self.assertEqual(attachment["public_summary"], "Public-safe attachment summary")
        for private_field in ["storage_key", "stored_filename", "original_filename", "checksum_sha256", "uploaded_by_role"]:
            self.assertNotIn(private_field, attachment)

        listed = self.client.get(f"/api/v1/drone/observations/{observation_id}/attachments")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["results"]), 1)

    def test_attachment_invalid_observation_rejected(self):
        self._enable_media_attachments()
        response = self.client.post(
            "/api/v1/drone/observations/missing-observation/attachments",
            json={"media_kind": "image", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(response.status_code, 404)

    def test_attachment_validation_rejects_unsupported_kind_visibility_and_paths(self):
        observation_id = self._create_observation()
        self._enable_media_attachments()
        unsupported_kind = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "zip_archive", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(unsupported_kind.status_code, 422)
        unsupported_visibility = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "review_visibility": "public_attachment_allowed", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(unsupported_visibility.status_code, 422)
        traversal = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "..\\private\\frame.jpg"},
        )
        self.assertEqual(traversal.status_code, 422)
        parent_reference = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "frame..jpg"},
        )
        self.assertEqual(parent_reference.status_code, 422)
        absolute_path = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "/tmp/frame.jpg"},
        )
        self.assertEqual(absolute_path.status_code, 422)
        windows_drive = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "C:\\private\\frame.jpg"},
        )
        self.assertEqual(windows_drive.status_code, 422)
        script_extension = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "original_filename": "frame.exe"},
        )
        self.assertEqual(script_extension.status_code, 422)

    def test_attachment_validation_rejects_bad_metadata_values(self):
        observation_id = self._create_observation()
        self._enable_media_attachments()
        invalid_review_status = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "analyst_review_status": "auto_reviewed", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(invalid_review_status.status_code, 422)
        invalid_release_status = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "public_release_status": "approved_public", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(invalid_release_status.status_code, 422)
        invalid_checksum = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "checksum_sha256": "not-a-sha256", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(invalid_checksum.status_code, 422)
        negative_size = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "file_size_bytes": -1, "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(negative_size.status_code, 422)
        huge_size = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "video", "file_size_bytes": 500_000_001, "original_filename": "frame-001.mp4", "mime_type": "video/mp4"},
        )
        self.assertEqual(huge_size.status_code, 422)
        malformed_timestamp = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "image", "captured_at": "not-a-date", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(malformed_timestamp.status_code, 422)
        unsafe_attachment_id = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"attachment_id": "../attachment", "media_kind": "image", "original_filename": "frame-001.jpg"},
        )
        self.assertEqual(unsafe_attachment_id.status_code, 422)

    def test_attachment_review_public_summary_safe(self):
        observation_id = self._create_observation()
        self._enable_media_attachments()
        created = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={"media_kind": "observation_note", "original_filename": "note.txt", "mime_type": "text/plain"},
        )
        self.assertEqual(created.status_code, 200)
        attachment_id = created.json()["attachment"]["attachment_id"]
        patch = self.client.patch(
            f"/api/v1/drone/observations/{observation_id}/attachments/{attachment_id}/review",
            json={
                "analyst_review_status": "reviewed",
                "review_visibility": "public_summary_only",
                "public_release_status": "inconclusive",
                "public_summary": "Attachment reviewed; no public media released.",
                "evidence_confidence": 0.4,
            },
        )
        self.assertEqual(patch.status_code, 200)
        attachment = patch.json()["attachment"]
        self.assertEqual(attachment["analyst_review_status"], "reviewed")
        self.assertEqual(attachment["review_visibility"], "public_summary_only")
        self.assertEqual(attachment["public_summary"], "Attachment reviewed; no public media released.")
        self.assertEqual(attachment["evidence_confidence"], 0.4)
        self.assertNotIn("storage_key", attachment)
        self.assertNotIn("original_filename", attachment)

    def test_attachments_do_not_create_sightings_or_alter_public_feed(self):
        observation_id = self._create_observation("water_clarity_observation")
        self._enable_media_attachments()
        before = json.dumps(self.client.get("/api/v1/drone/surveillance-feed").json(), sort_keys=True)
        response = self.client.post(
            f"/api/v1/drone/observations/{observation_id}/attachments",
            json={
                "media_kind": "image",
                "media_reference_type": "local_filename",
                "original_filename": "private-frame.jpg",
                "public_summary": "Private image retained for analyst review.",
            },
        )
        self.assertEqual(response.status_code, 200)
        after_payload = self.client.get("/api/v1/drone/surveillance-feed").json()
        after = json.dumps(after_payload, sort_keys=True)
        self.assertEqual(before, after)
        self.assertNotIn("private-frame.jpg", after)
        self.assertNotIn("attachment_id", after)
        self.assertNotIn("storage_key", after)
        self.assertFalse(response.json()["sighting_created"])

    def test_mission_completion(self):
        self._create_mission()
        response = self.client.post("/api/v1/drone/missions/mission-test-drone/complete", json={"ended_at": "2099-06-08T18:00:00Z"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mission"]["status"], "completed")


