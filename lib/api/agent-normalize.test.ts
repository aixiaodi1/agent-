import { describe, expect, it } from "vitest";
import { normalizeAgentRun } from "./agent-client";

describe("normalizeAgentRun", () => {
  it("fills optional collection fields with empty arrays", () => {
    const run = normalizeAgentRun({
      id: "run_test",
      mode: "real",
      prompt: "Trace this agent",
      status: "succeeded",
      requestJson: { prompt: "Trace this agent" },
      responseJson: { ok: true },
      finalAnswer: "Done"
    });

    expect(run.nodes).toEqual([]);
    expect(run.events).toEqual([]);
    expect(run.toolCalls).toEqual([]);
    expect(run.vectorMatches).toEqual([]);
  });

  it("rejects malformed agent run responses", () => {
    expect(() => normalizeAgentRun({ status: "succeeded" })).toThrow(
      "Invalid agent run response"
    );
  });
});
