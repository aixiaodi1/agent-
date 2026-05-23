import { Database, History, ServerCog } from "lucide-react";
import type { AgentApiMode, AgentRun } from "@/lib/types/agent";
import { StatusPill } from "./status-pill";

interface LeftRailProps {
  apiMode: AgentApiMode;
  run: AgentRun;
  onModeChange: (mode: AgentApiMode) => void;
}

export function LeftRail({ apiMode, run, onModeChange }: LeftRailProps) {
  return (
    <aside className="left-rail">
      <div>
        <p className="eyebrow">Agent Debug</p>
        <h1>LangGraph Trace Workbench</h1>
      </div>

      <section className="rail-section">
        <div className="section-heading">
          <ServerCog aria-hidden="true" size={16} />
          <span>API Mode</span>
        </div>
        <div className="segmented" aria-label="API mode">
          <button
            className={apiMode === "mock" ? "active" : ""}
            type="button"
            onClick={() => onModeChange("mock")}
          >
            Mock
          </button>
          <button
            className={apiMode === "real" ? "active" : ""}
            type="button"
            onClick={() => onModeChange("real")}
          >
            FastAPI
          </button>
        </div>
      </section>

      <section className="rail-section">
        <div className="section-heading">
          <Database aria-hidden="true" size={16} />
          <span>Agent Profile</span>
        </div>
        <dl className="meta-list">
          <div>
            <dt>Agent</dt>
            <dd>{String(run.requestJson.agentId ?? "research-agent")}</dd>
          </div>
          <div>
            <dt>VectorDB</dt>
            <dd>{String(run.requestJson.vectorProvider ?? "qdrant")}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              <StatusPill status={run.status} />
            </dd>
          </div>
        </dl>
      </section>

      <section className="rail-section rail-grow">
        <div className="section-heading">
          <History aria-hidden="true" size={16} />
          <span>Recent Runs</span>
        </div>
        <button className="run-card active" type="button">
          <span>{run.id}</span>
          <small>{run.latencyMs ?? 0} ms</small>
        </button>
      </section>
    </aside>
  );
}
