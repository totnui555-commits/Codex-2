import { describe, it, expect } from "vitest";
import { agentState, money, type Snapshot } from "./domain";
describe("authoritative office state", () => {
  it("does not animate idle roles as working", () =>
    expect(
      agentState("frontend_engineer", { runs: [] } as unknown as Snapshot),
    ).toBe("idle"));
  it("uses persisted running and quarantine states", () => {
    expect(
      agentState("frontend_engineer", {
        runs: [{ agent_role: "frontend_engineer", status: "running" }],
      } as unknown as Snapshot),
    ).toBe("coding");
    expect(
      agentState("frontend_engineer", {
        runs: [{ agent_role: "frontend_engineer", status: "quarantined" }],
      } as unknown as Snapshot),
    ).toBe("quarantined");
  });
  it("formats THB without mixing forecast and revenue", () =>
    expect(money(2000)).toContain("2,000"));
});
