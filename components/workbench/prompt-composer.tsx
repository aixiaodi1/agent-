import { Play, SquareTerminal } from "lucide-react";
import type { AgentApiMode } from "@/lib/types/agent";

interface PromptComposerProps {
  prompt: string;
  apiMode: AgentApiMode;
  isRunning: boolean;
  onPromptChange: (prompt: string) => void;
  onRun: () => void;
}

export function PromptComposer({
  prompt,
  apiMode,
  isRunning,
  onPromptChange,
  onRun
}: PromptComposerProps) {
  const canRun = prompt.trim().length > 0 && !isRunning;

  return (
    <section className="prompt-composer">
      <div className="composer-topline">
        <label htmlFor="prompt">Prompt</label>
        <span>
          <SquareTerminal aria-hidden="true" size={15} />
          {apiMode === "mock" ? "Mock run" : "FastAPI run"}
        </span>
      </div>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(event) => onPromptChange(event.target.value)}
        rows={4}
      />
      <div className="composer-actions">
        <span>{prompt.trim() ? "Ready" : "Enter a prompt to run"}</span>
        <button type="button" onClick={onRun} disabled={!canRun}>
          <Play aria-hidden="true" size={16} />
          {isRunning ? "Running" : "Run"}
        </button>
      </div>
    </section>
  );
}
