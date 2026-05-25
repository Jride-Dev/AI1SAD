import { describe, expect, it } from "vitest";

import { getDashboardData } from "./client";

describe("dashboard API client", () => {
  it("returns mock dashboard data without a backend", async () => {
    const data = await getDashboardData({ lat: -31.983, lon: 115.515 });

    expect(data.warning.warning_score).toBeGreaterThanOrEqual(0);
    expect(data.surveillance.zones.length).toBeGreaterThan(0);
    expect(data.alerts[0].recommended_action).toContain("drone");
    expect(data.providerHealth.some((provider) => provider.provider === "vessel_fishing_static")).toBe(true);
    expect(data.replay.signal_decay_timeline.length).toBeGreaterThan(0);
  });
});
