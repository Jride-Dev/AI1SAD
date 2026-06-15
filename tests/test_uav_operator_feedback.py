from __future__ import annotations

import json
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import COLLECTIONS, get_database
from app.services.uav_operator_feedback import public_feedback_doc
from tests.test_public_api_privacy import FakeDB


class UavOperatorFeedbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = FakeDB()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_database] = lambda: self.db
        self.client = TestClient(app)

    def valid_payload(self) -> dict:
        return {
            "submitter_role": "uav_operator",
            "organization_type": "lifeguard_service",
            "region": "Sydney eastern suburbs",
            "country": "Australia",
            "contact_allowed": True,
            "contact_reference": "ops-desk-private-reference",
            "drone_platform": "consumer quadcopter",
            "drone_model": "generic coastal patrol aircraft",
            "flight_app": "manual flight app",
            "telemetry_available": "export_file",
            "telemetry_export_format": "csv",
            "media_workflow": "sd_card",
            "no_sighting_patrols_logged": True,
            "observation_fields_used": ["timestamp", "location", "visibility"],
            "privacy_constraints": ["do not publish operator identity"],
            "controlled_airspace_notes": "Airport review required for some patrol areas.",
            "operator_pain_points": ["manual field duplication"],
            "requested_features": ["offline checklist"],
            "suggested_observation_types": ["no_sighting_patrol_result"],
            "workflow_notes": "Feedback from field workflow review.",
            "public_summary": "Operator wants structured requirements intake for patrol workflow notes.",
            "internal_notes_private": "Private follow-up details stay internal.",
            "requirements_tags": ["uav_workflow", "requirements"],
        }

    def test_feedback_submission_accepted_with_valid_payload(self):
        response = self.client.post("/api/v1/uav/operator-feedback", json=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        feedback = payload["feedback"]
        self.assertEqual(payload["status"], "created")
        self.assertTrue(payload["research_input_only"])
        self.assertFalse(payload["creates_sighting"])
        self.assertFalse(payload["creates_public_alert"])
        self.assertFalse(payload["alters_scoring"])
        self.assertFalse(payload["alters_replay"])
        self.assertEqual(feedback["submitter_role"], "uav_operator")
        self.assertEqual(feedback["review_status"], "new")

    def test_unsupported_enum_rejected(self):
        payload = self.valid_payload()
        payload["submitter_role"] = "drone_vendor_partner"
        response = self.client.post("/api/v1/uav/operator-feedback", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_overlong_notes_rejected(self):
        payload = self.valid_payload()
        payload["workflow_notes"] = "x" * 1201
        response = self.client.post("/api/v1/uav/operator-feedback", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_unsafe_contact_and_public_summary_values_rejected(self):
        payload = self.valid_payload()
        payload["contact_reference"] = "javascript:alert(1)"
        response = self.client.post("/api/v1/uav/operator-feedback", json=payload)
        self.assertEqual(response.status_code, 422)

        payload = self.valid_payload()
        payload["public_summary"] = "Email operator@example.com for private details"
        public_contact = self.client.post("/api/v1/uav/operator-feedback", json=payload)
        self.assertEqual(public_contact.status_code, 422)

        payload = self.valid_payload()
        payload["internal_notes_private"] = "api_key=1234567890abcdef"
        secret = self.client.post("/api/v1/uav/operator-feedback", json=payload)
        self.assertEqual(secret.status_code, 422)

    def test_contact_reference_private_field_excluded_from_public_output(self):
        response = self.client.post("/api/v1/uav/operator-feedback", json=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        text = json.dumps(response.json(), sort_keys=True)
        self.assertNotIn("ops-desk-private-reference", text)
        self.assertNotIn("contact_reference", text)
        self.assertNotIn("internal_notes_private", text)
        self.assertNotIn("reviewer_role", text)
        stored = self.db[COLLECTIONS["uav_operator_feedback"]].docs[0]
        public = public_feedback_doc(stored)
        self.assertNotIn("contact_reference", public)
        self.assertNotIn("internal_notes_private", public)

    def test_feedback_does_not_create_observation_sighting_or_feed_item(self):
        before_observations = len(self.db[COLLECTIONS["drone_observations"]].docs)
        before_sightings = len(self.db[COLLECTIONS["sighting_reports"]].docs)
        response = self.client.post("/api/v1/uav/operator-feedback", json=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.db[COLLECTIONS["drone_observations"]].docs), before_observations)
        self.assertEqual(len(self.db[COLLECTIONS["sighting_reports"]].docs), before_sightings)
        feed = self.client.get("/api/v1/drone/surveillance-feed")
        self.assertEqual(feed.status_code, 200)
        self.assertNotIn("uav_operator_feedback", json.dumps(feed.json()))

    def test_feedback_does_not_alter_scoring_or_replay_outputs(self):
        warning_before = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true").json()
        replay_before = self.client.get("/api/v1/replay/library").json()
        response = self.client.post("/api/v1/uav/operator-feedback", json=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        warning_after = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true").json()
        replay_after = self.client.get("/api/v1/replay/library").json()
        self.assertEqual(warning_before["warning_score"], warning_after["warning_score"])
        self.assertEqual(warning_before["warning_band"], warning_after["warning_band"])
        self.assertEqual(warning_before["activity_context_score"], warning_after["activity_context_score"])
        self.assertEqual([item["id"] for item in replay_before["results"]], [item["id"] for item in replay_after["results"]])

    def test_review_status_patch_validates_enum_and_filters_private_notes(self):
        created = self.client.post("/api/v1/uav/operator-feedback", json=self.valid_payload())
        self.assertEqual(created.status_code, 200)
        feedback_id = created.json()["feedback"]["feedback_id"]
        invalid = self.client.patch(f"/api/v1/uav/operator-feedback/{feedback_id}/status", json={"review_status": "published"})
        self.assertEqual(invalid.status_code, 422)

        valid = self.client.patch(
            f"/api/v1/uav/operator-feedback/{feedback_id}/status",
            json={
                "review_status": "triaged",
                "requirements_tags": ["field_requirements"],
                "internal_notes_private": "Private triage note",
                "reviewer_role": "analyst",
            },
        )
        self.assertEqual(valid.status_code, 200)
        payload = valid.json()["feedback"]
        self.assertEqual(payload["review_status"], "triaged")
        self.assertNotIn("Private triage note", json.dumps(valid.json()))
        self.assertNotIn("reviewer_role", json.dumps(valid.json()))


if __name__ == "__main__":
    unittest.main()
