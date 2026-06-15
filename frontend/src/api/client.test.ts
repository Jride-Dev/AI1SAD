import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { __setMockModeForTests, getAlerts, getDashboardData, getDroneConsoleData, submitDroneObservation, getWarning } from "./client";

describe("dashboard API client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    __setMockModeForTests(null);
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("returns mock dashboard data without a backend", async () => {
    __setMockModeForTests(true);
    const data = await getDashboardData({ lat: -31.983, lon: 115.515 });

    expect(data.warning.warning_score).toBeGreaterThanOrEqual(0);
    expect(data.surveillance.zones.length).toBeGreaterThan(0);
    expect(data.alerts[0].recommended_action).toContain("drone");
    expect(data.providerHealth.some((provider) => provider.provider === "vessel_fishing_static")).toBe(true);
    expect(data.replay.signal_decay_timeline.length).toBeGreaterThan(0);
    expect(data.replayLibrary.map((item) => item.id)).toContain("horseshoe_reef_2026");
    expect(data.replayHeatmap.cells[0].surveillance_priority_score).toBeGreaterThanOrEqual(0);
    expect(data.demoScenarios.map((scenario) => scenario.scenario_id)).toContain("queensland_spearfishing_reef_tiger_bull_2026");
    expect(data.demoStatus.demo_mode).toBe(true);
    expect(data.data_source).toBe("mock");
  });

  it("surfaces an error when mock mode is disabled and fetch fails", async () => {
    __setMockModeForTests(false);
    fetchMock.mockRejectedValueOnce(new Error("network down"));
    await expect(getWarning({ lat: -31.983, lon: 115.515 })).rejects.toThrow("network down");
  });

  it("does not silently use mock fallback on backend 500", async () => {
    __setMockModeForTests(false);
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });
    await expect(getWarning({ lat: -31.983, lon: 115.515 })).rejects.toThrow("Request failed (500)");
  });

  it("does not silently use mock fallback on malformed payload", async () => {
    __setMockModeForTests(false);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ unexpected: true }),
    });
    await expect(getAlerts()).rejects.toThrow("Malformed API payload");
  });

  it("returns drone console demo data only when mock mode is enabled", async () => {
    __setMockModeForTests(true);
    const data = await getDroneConsoleData();

    expect(data.data_source).toBe("mock");
    expect(data.missions[0].mission.autonomous_flight_control).toBe(false);
    expect(data.feed.flight_control?.commands_exposed).toBe(false);
  });

  it("submits drone observations in explicit mock mode", async () => {
    __setMockModeForTests(true);
    const observation = await submitDroneObservation("mission-panama-city-mavlink-demo", {
      timestamp: "2026-06-08T17:10:00Z",
      latitude: 30.1826,
      longitude: -85.7539,
      observation_type: "no_sighting_patrol_result",
      count: 0,
      confidence: 0.6,
      review_status: "operator_reviewed",
      source: "drone_operator_visual",
      source_type: "drone_operator",
      public_visibility: true,
    });

    expect(observation.mission_id).toBe("mission-panama-city-mavlink-demo");
    expect(observation.observation_type).toBe("no_sighting_patrol_result");
  });

  it("surfaces backend validation errors for drone observation submit", async () => {
    __setMockModeForTests(false);
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({ detail: "latitude must be between -90 and 90" }),
    });

    await expect(
      submitDroneObservation("mission-test", {
        timestamp: "2026-06-08T17:10:00Z",
        latitude: 95,
        longitude: -85.7539,
        observation_type: "shark_sighting",
        confidence: 0.6,
        review_status: "operator_reviewed",
        source: "drone_operator_visual",
        source_type: "drone_operator",
        public_visibility: true,
      }),
    ).rejects.toThrow("latitude must be between -90 and 90");
  });

  it("does not silently mock drone console data when live backend is unavailable", async () => {
    __setMockModeForTests(false);
    fetchMock.mockRejectedValueOnce(new Error("backend unavailable"));
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ results: [] }) });

    await expect(getDroneConsoleData()).rejects.toThrow("backend unavailable");
  });
});
