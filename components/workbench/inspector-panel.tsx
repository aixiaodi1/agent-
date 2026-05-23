import { Braces, Database, Wrench } from "lucide-react";
import type {
  AgentNode,
  AgentToolCall,
  AgentTraceEvent,
  AgentVectorMatch
} from "@/lib/types/agent";
import { JsonViewer } from "./json-viewer";
import { StatusPill } from "./status-pill";

interface InspectorPanelProps {
  node?: AgentNode;
  event?: AgentTraceEvent;
  toolCalls: AgentToolCall[];
  vectorMatches: AgentVectorMatch[];
  requestJson: Record<string, unknown>;
  responseJson: Record<string, unknown>;
}

export function InspectorPanel({
  node,
  event,
  toolCalls,
  vectorMatches,
  requestJson,
  responseJson
}: InspectorPanelProps) {
  const relatedTools = node
    ? toolCalls.filter((toolCall) => toolCall.nodeId === node.id)
    : toolCalls;
  const relatedMatches = node
    ? vectorMatches.filter((match) => match.nodeId === node.id)
    : vectorMatches;

  return (
    <aside className="inspector">
      <section className="inspector-section">
        <div className="section-heading">
          <Braces aria-hidden="true" size={16} />
          <span>Selected Node</span>
        </div>
        {node ? (
          <div className="node-detail">
            <div>
              <strong>{node.label}</strong>
              <StatusPill status={node.status} />
            </div>
            <p>{node.stateSummary}</p>
            <small>{node.durationMs ?? 0} ms</small>
          </div>
        ) : (
          <p className="empty-state">No node selected.</p>
        )}
      </section>

      <section className="inspector-section">
        <div className="section-heading">
          <Wrench aria-hidden="true" size={16} />
          <span>Tool Calls</span>
        </div>
        {relatedTools.length ? (
          relatedTools.map((toolCall) => (
            <article className="detail-card" key={toolCall.id}>
              <strong>{toolCall.name}</strong>
              <p>{toolCall.resultPreview}</p>
              <small>{toolCall.durationMs} ms</small>
            </article>
          ))
        ) : (
          <p className="empty-state">No tool calls for this node.</p>
        )}
      </section>

      <section className="inspector-section">
        <div className="section-heading">
          <Database aria-hidden="true" size={16} />
          <span>VectorDB Matches</span>
        </div>
        {relatedMatches.length ? (
          relatedMatches.map((match) => (
            <article className="detail-card" key={match.id}>
              <strong>{match.title}</strong>
              <p>{match.contentPreview}</p>
              <small>
                {match.provider} · {match.collection} · {match.score.toFixed(2)}
              </small>
            </article>
          ))
        ) : (
          <p className="empty-state">No vector matches for this node.</p>
        )}
      </section>

      <JsonViewer label="Selected Event JSON" value={event?.payload ?? {}} />
      <JsonViewer label="Request JSON" value={requestJson} />
      <JsonViewer label="Response JSON" value={responseJson} />
    </aside>
  );
}
