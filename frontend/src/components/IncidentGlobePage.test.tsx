import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { IncidentGlobePage } from "./IncidentGlobePage";


describe("IncidentGlobePage", () => {
  it("offers the non-overlapping 1990s layer", () => {
    const markup = renderToString(<IncidentGlobePage />);

    expect(markup).toContain("Shark incidents, 1990–2026");
    expect(markup).toContain("All 1990–2026");
    expect(markup).toContain("1990s");
  });
});
