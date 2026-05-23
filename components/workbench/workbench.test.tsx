import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getInitialMockRun } from "@/lib/mock/agent-runs";
import { AgentWorkbench } from "./workbench";

describe("AgentWorkbench", () => {
  it("renders the trace workbench with mock run details", () => {
    render(<AgentWorkbench initialRun={getInitialMockRun()} />);

    expect(
      screen.getByRole("heading", { name: "LangGraph Trace Workbench" })
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Prompt")).toBeInTheDocument();
    expect(screen.getByText("retrieve_context")).toBeInTheDocument();
    expect(screen.getByText("LangGraph routing policy")).toBeInTheDocument();
    expect(
      screen.getByText(/这次 Agent 先进入 retrieve_context/)
    ).toBeInTheDocument();
  });
});
