import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { mockDroneConsoleData } from "../api/mockData";
import { DroneOperatorConsole, buildDroneObservationPayload, toApiObservationType, validateDroneObservationForm } from "./DroneOperatorConsole";

const validForm = {
  mission_id: "mission-test",
  observation_type: "SHARK_SIGHTING",
  observed_at: "2026-06-08T17:10",
  latitude: "30.1826",
  longitude: "-85.7539",
  observer_role: "drone_operator",
  visual_confidence: "0.7",
  provenance: "drone_operator_visual",
  estimated_size_m: "2.4",
  estimated_count: "1",
  species_guess: "bull shark",
  species_confidence: "0.55",
  behavior_notes: "Moving parallel to shore",
  visibility_notes: "Clear enough for visual review",
  surf_zone_notes: "Moderate surf-line activity",
  media_reference: "local-ref-001",
  operator_notes: "Operator note stays internal",
  public_summary: "Public-safe summary",
  public_visibility: true,
};

describe("DroneOperatorConsole", () => {
  it("renders console safety copy and observation type selector", () => {
    const markup = renderToString(<DroneOperatorConsole initialData={mockDroneConsoleData} />);

    expect(markup).toContain("Drone Operator Console");
    expect(markup).toContain("SHARK_SIGHTING");
    expect(markup).toContain("NO_SIGHTING_PATROL");
    expect(markup).toContain("AI1SAD records human observations");
    expect(markup).toContain("No-sighting patrols reduce uncertainty only within the observed patrol area");
    expect(markup).toContain("Species guesses are provisional");
  });

  it("maps public observation labels to existing backend enum values", () => {
    expect(toApiObservationType("SHARK_SIGHTING")).toBe("shark_sighting");
    expect(toApiObservationType("NO_SIGHTING_PATROL")).toBe("no_sighting_patrol_result");
    expect(toApiObservationType("POOR_VISIBILITY")).toBe("water_clarity_observation");
    expect(toApiObservationType("OTHER")).toBe("other");
  });

  it("validates required fields and coordinate bounds", () => {
    const errors = validateDroneObservationForm({ ...validForm, mission_id: "", latitude: "91", provenance: "" });

    expect(errors).toContain("Mission is required.");
    expect(errors).toContain("Latitude must be between -90 and 90.");
    expect(errors).toContain("Provenance is required.");
  });

  it("builds a bounded observation payload for successful submit", () => {
    const payload = buildDroneObservationPayload(validForm);

    expect(payload.observation_type).toBe("shark_sighting");
    expect(payload.source).toBe("drone_operator_visual");
    expect(payload.source_type).toBe("drone_operator");
    expect(payload.confidence).toBe(0.7);
    expect(payload.probable_species).toBe("bull shark");
    expect(payload.species_assessment_source).toBe("operator_visual_assessment");
    expect(payload.internal_notes).toBe("Operator note stays internal");
  });

  it("keeps no-sighting patrol count at zero and does not imply safety", () => {
    const payload = buildDroneObservationPayload({ ...validForm, observation_type: "NO_SIGHTING_PATROL", estimated_count: "5" });

    expect(payload.observation_type).toBe("no_sighting_patrol_result");
    expect(payload.count).toBe(0);
  });

  it("renders analyst review panel with pending observations when analyst_review_status is missing or unreviewed", () => {
    const markup = renderToString(<DroneOperatorConsole initialData={mockDroneConsoleData} />);

    expect(markup).toContain("Analyst Review");
    expect(markup).toContain("Review Queue");
    expect(markup).toContain("pending");
    expect(markup).toContain("no sighting patrol result");
    expect(markup).toContain("shark sighting");
  });

  it("renders review status dropdown with valid options", () => {
    const markup = renderToString(<DroneOperatorConsole initialData={mockDroneConsoleData} />);

    expect(markup).toContain("unreviewed");
    expect(markup).toContain("needs_review");
    expect(markup).toContain("in_review");
    expect(markup).toContain("reviewed");
    expect(markup).toContain("rejected");
    expect(markup).toContain("inconclusive");
  });

  it("renders review outcomes dropdown with valid options", () => {
    const markup = renderToString(<DroneOperatorConsole initialData={mockDroneConsoleData} />);

    expect(markup).toContain("no_public_change");
    expect(markup).toContain("confirms_operator_observation");
    expect(markup).toContain("downgrades_operator_observation");
    expect(markup).toContain("upgrades_operator_observation");
    expect(markup).toContain("species_uncertain");
    expect(markup).toContain("false_positive");
    expect(markup).toContain("duplicate");
    expect(markup).toContain("unusable_media");
  });

  it("analyst review private notes warning is present", () => {
    const markup = renderToString(<DroneOperatorConsole initialData={mockDroneConsoleData} />);

    expect(markup).toContain("Private Notes (never public)");
    expect(markup).toContain("Analyst notes remain private and are never returned in public feed output.");
  });
});
