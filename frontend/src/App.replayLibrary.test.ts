import { describe, expect, it } from "vitest";

import { resolveReplaySelectionId } from "./App";
import { mockReplayLibrary } from "./api/mockData";

describe("replay library selection", () => {
  it("keeps selection when the id still exists", () => {
    const selected = resolveReplaySelectionId("horseshoe_reef_2026", mockReplayLibrary);
    expect(selected).toBe("horseshoe_reef_2026");
  });

  it("resets to first item when selected id is no longer present", () => {
    const refreshed = [mockReplayLibrary[2], mockReplayLibrary[3]];
    const selected = resolveReplaySelectionId("horseshoe_reef_2026", refreshed);
    expect(selected).toBe(refreshed[0].id);
  });

  it("returns empty selection for empty library payload", () => {
    expect(resolveReplaySelectionId("horseshoe_reef_2026", [])).toBe("");
  });
});
