import type { AgentRun } from "@/lib/types/agent";

const startedAt = "2026-05-23T06:10:00.000Z";
const finishedAt = "2026-05-23T06:10:02.420Z";

export const mockAgentRun: AgentRun = {
  id: "run_mock_001",
  mode: "mock",
  prompt: "帮我检查 LangGraph Agent 为什么先检索再调用工具。",
  status: "succeeded",
  startedAt,
  finishedAt,
  latencyMs: 2420,
  tokens: {
    prompt: 812,
    completion: 468,
    total: 1280
  },
  nodes: [
    {
      id: "start",
      label: "Start",
      status: "succeeded",
      startedAt,
      finishedAt: "2026-05-23T06:10:00.120Z",
      durationMs: 120,
      stateSummary: "Accepted prompt and initialized debug state."
    },
    {
      id: "retrieve_context",
      label: "Retrieve Context",
      status: "succeeded",
      startedAt: "2026-05-23T06:10:00.130Z",
      finishedAt: "2026-05-23T06:10:00.740Z",
      durationMs: 610,
      stateSummary: "Loaded 3 vector matches from qdrant knowledge_base."
    },
    {
      id: "call_tool",
      label: "Call Tool",
      status: "succeeded",
      startedAt: "2026-05-23T06:10:00.760Z",
      finishedAt: "2026-05-23T06:10:01.360Z",
      durationMs: 600,
      stateSummary: "Called inspect_trace with current graph state."
    },
    {
      id: "generate_answer",
      label: "Generate Answer",
      status: "succeeded",
      startedAt: "2026-05-23T06:10:01.390Z",
      finishedAt: "2026-05-23T06:10:02.310Z",
      durationMs: 920,
      stateSummary: "Generated final response with retrieved context and tool output."
    },
    {
      id: "end",
      label: "End",
      status: "succeeded",
      startedAt: "2026-05-23T06:10:02.320Z",
      finishedAt,
      durationMs: 100,
      stateSummary: "Persisted trace payload and completed run."
    }
  ],
  events: [
    {
      id: "evt_start",
      nodeId: "start",
      type: "node_start",
      timestamp: startedAt,
      title: "Run started",
      detail: "LangGraph state initialized.",
      payload: { threadId: "thread_mock_001", debug: true }
    },
    {
      id: "evt_retrieval",
      nodeId: "retrieve_context",
      type: "retrieval",
      timestamp: "2026-05-23T06:10:00.720Z",
      title: "Vector search returned 3 matches",
      detail: "Top hit explains the retrieval-before-tool policy.",
      payload: { provider: "qdrant", collection: "knowledge_base", matches: 3 }
    },
    {
      id: "evt_tool",
      nodeId: "call_tool",
      type: "tool_call",
      timestamp: "2026-05-23T06:10:01.220Z",
      title: "inspect_trace completed",
      detail: "Tool returned state transition analysis.",
      payload: { tool: "inspect_trace", status: "succeeded" }
    },
    {
      id: "evt_generate",
      nodeId: "generate_answer",
      type: "token_stream",
      timestamp: "2026-05-23T06:10:01.900Z",
      title: "Streaming final answer",
      detail: "Completion tokens streamed to the client.",
      payload: { tokens: 468 }
    },
    {
      id: "evt_final",
      nodeId: "end",
      type: "final_answer",
      timestamp: finishedAt,
      title: "Final answer ready",
      detail: "Run completed successfully.",
      payload: { status: "succeeded" }
    }
  ],
  toolCalls: [
    {
      id: "tool_001",
      nodeId: "call_tool",
      name: "inspect_trace",
      status: "succeeded",
      arguments: {
        runId: "run_mock_001",
        includeStateDiff: true
      },
      durationMs: 418,
      resultPreview: "The graph retrieves context before tool execution because the router classified the prompt as knowledge-dependent."
    }
  ],
  vectorMatches: [
    {
      id: "vec_001",
      nodeId: "retrieve_context",
      provider: "qdrant",
      collection: "knowledge_base",
      score: 0.92,
      title: "LangGraph routing policy",
      contentPreview: "Knowledge-dependent prompts should retrieve context before invoking diagnostic tools.",
      metadata: {
        source: "agent_playbook.md",
        chunk: 12
      }
    },
    {
      id: "vec_002",
      nodeId: "retrieve_context",
      provider: "qdrant",
      collection: "knowledge_base",
      score: 0.87,
      title: "Trace inspection contract",
      contentPreview: "The inspect_trace tool expects node ids, state summaries, and timing metadata.",
      metadata: {
        source: "tool_contracts.md",
        chunk: 4
      }
    }
  ],
  requestJson: {
    prompt: "帮我检查 LangGraph Agent 为什么先检索再调用工具。",
    agentId: "research-agent",
    threadId: "thread_mock_001",
    vectorProvider: "qdrant",
    debug: true
  },
  responseJson: {
    id: "run_mock_001",
    status: "succeeded",
    latencyMs: 2420,
    nodes: 5,
    vectorMatches: 2
  },
  finalAnswer:
    "这次 Agent 先进入 retrieve_context，是因为路由器把问题判定为需要知识库上下文。随后 call_tool 节点拿到检索摘要再调用 inspect_trace，因此工具输入更完整。"
};

export function getInitialMockRun(): AgentRun {
  return structuredClone(mockAgentRun);
}
