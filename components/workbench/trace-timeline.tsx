import type { AgentTraceEvent } from "@/lib/types/agent";

interface TraceTimelineProps {
  events: AgentTraceEvent[];
  selectedEventId?: string;
  onSelectEvent: (event: AgentTraceEvent) => void;
}

export function TraceTimeline({
  events,
  selectedEventId,
  onSelectEvent
}: TraceTimelineProps) {
  return (
    <section className="trace-panel">
      <div className="panel-title">Trace Timeline</div>
      <div className="event-list">
        {events.map((event) => (
          <button
            className={event.id === selectedEventId ? "event-row active" : "event-row"}
            key={event.id}
            type="button"
            onClick={() => onSelectEvent(event)}
          >
            <span>{event.type}</span>
            <strong>{event.title}</strong>
            <small>{event.detail}</small>
          </button>
        ))}
      </div>
    </section>
  );
}
