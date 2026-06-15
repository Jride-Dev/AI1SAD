import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { UavFeedbackPage, buildUavFeedbackPayload, validateUavFeedbackForm } from "./UavFeedbackPage";

const validForm = {
  submitter_role: "uav_operator",
  organization_type: "lifeguard_service",
  region: "Sydney eastern suburbs",
  country: "Australia",
  contact_allowed: true,
  contact_reference: "private-follow-up-reference",
  drone_platform: "consumer quadcopter",
  drone_model: "generic patrol platform",
  flight_app: "manual flight app",
  telemetry_available: "export_file",
  telemetry_export_format: "csv",
  media_workflow: "sd_card",
  no_sighting_patrols_logged: true,
  observation_fields_used: "timestamp, location, visibility",
  privacy_constraints: "do not publish operator identity",
  controlled_airspace_notes: "Airport review required near some beaches",
  operator_pain_points: "duplicate logging",
  requested_features: "offline checklist",
  suggested_observation_types: "no_sighting_patrol_result",
  workflow_notes: "Research feedback only.",
  public_summary: "Operator wants structured patrol workflow feedback intake.",
  internal_notes_private: "Private note",
  requirements_tags: "uav_workflow, telemetry",
};

describe("UavFeedbackPage", () => {
  it("renders required safety and privacy copy", () => {
    const markup = renderToString(<UavFeedbackPage />);

    expect(markup).toContain("Operator Feedback Intake");
    expect(markup).toContain("Feedback records are research inputs, not live surveillance observations.");
    expect(markup).toContain("Submitting feedback does not create a sighting, warning, or public alert.");
    expect(markup).toContain("Contact details are optional and private by default.");
  });

  it("builds a valid research-only feedback payload", () => {
    const payload = buildUavFeedbackPayload(validForm);

    expect(payload.submitter_role).toBe("uav_operator");
    expect(payload.telemetry_available).toBe("export_file");
    expect(payload.no_sighting_patrols_logged).toBe(true);
    expect(payload.observation_fields_used).toEqual(["timestamp", "location", "visibility"]);
    expect(payload.requirements_tags).toEqual(["uav_workflow", "telemetry"]);
  });

  it("validates unsupported values and private public-summary leakage", () => {
    const errors = validateUavFeedbackForm({
      ...validForm,
      submitter_role: "vendor_partner",
      media_workflow: "public_video_url",
      public_summary: "Contact operator@example.com",
    });

    expect(errors).toContain("Submitter role is not supported.");
    expect(errors).toContain("Media workflow is not supported.");
    expect(errors).toContain("Public summary must not include contact details.");
  });

  it("shows backend unavailable state", () => {
    const markup = renderToString(<UavFeedbackPage initialError="backend unavailable" />);

    expect(markup).toContain("UAV feedback backend unavailable.");
    expect(markup).toContain("backend unavailable");
  });
});
