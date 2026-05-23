import type { AgentNodeStatus, AgentRunStatus } from "@/lib/types/agent";

type Status = AgentNodeStatus | AgentRunStatus;

const statusLabels: Record<Status, string> = {
  idle: "Idle",
  pending: "Pending",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed"
};

export function StatusPill({ status }: { status: Status }) {
  return <span className={`status-pill status-${status}`}>{statusLabels[status]}</span>;
}
