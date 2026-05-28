import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { mockDashboardData } from "../api/mockData";
import { OperationalMap } from "./OperationalMap";

describe("OperationalMap", () => {
  it("renders the mock-mode map shell and scenario selector", () => {
    const markup = renderToString(
      <OperationalMap data={mockDashboardData} selectedScenarioId="horseshoe_reef_2026" onSelectScenario={vi.fn()} />,
    );

    expect(markup).toContain("Why This Zone?");
    expect(markup).toContain("Horseshoe Reef 2026");
    expect(markup).toContain("Replay heatmap");
    expect(markup).toContain("Surveillance Priority");
    expect(markup).toContain("Low warning can coexist with high surveillance priority");
  });
});
