import { getInitialMockRun } from "@/lib/mock/agent-runs";
import {
  AgentRunError,
  type AgentApiMode,
  type AgentRun,
  type CreateAgentRunInput
} from "@/lib/types/agent";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function normalizeAgentRun(value: unknown): AgentRun {
  if (!isRecord(value)) {
    throw new Error("Invalid agent run response");
  }

  const { id, mode, prompt, status, finalAnswer } = value;

  if (
    typeof id !== "string" ||
    (mode !== "mock" && mode !== "real") ||
    typeof prompt !== "string" ||
    typeof status !== "string" ||
    typeof finalAnswer !== "string"
  ) {
    throw new Error("Invalid agent run response");
  }

  const run = value as unknown as AgentRun;

  return {
    ...run,
    nodes: Array.isArray(value.nodes) ? value.nodes : [],
    events: Array.isArray(value.events) ? value.events : [],
    toolCalls: Array.isArray(value.toolCalls) ? value.toolCalls : [],
    vectorMatches: Array.isArray(value.vectorMatches) ? value.vectorMatches : [],
    requestJson: isRecord(value.requestJson) ? value.requestJson : {},
    responseJson: isRecord(value.responseJson) ? value.responseJson : {}
  };
}

export interface CreateAgentRunOptions {
  mode?: AgentApiMode;
}

export async function createAgentRun(
  input: CreateAgentRunInput,
  options: CreateAgentRunOptions = {}
): Promise<AgentRun> {
  const mode = options.mode ?? "mock";

  if (mode === "mock") {
    const now = new Date().toISOString();
    const mockRun = getInitialMockRun();

    return normalizeAgentRun({
      ...mockRun,
      id: `run_mock_${Date.now()}`,
      mode: "mock",
      prompt: input.prompt,
      startedAt: now,
      finishedAt: now,
      requestJson: input,
      responseJson: {
        ...mockRun.responseJson,
        mode: "mock",
        prompt: input.prompt
      }
    });
  }

  const response = await fetch("/api/agent/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      isRecord(payload) && typeof payload.message === "string"
        ? payload.message
        : "Agent run request failed";

    throw new AgentRunError(message, response.status, payload);
  }

  return normalizeAgentRun(payload);
}
