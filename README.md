# LangGraph Trace Workbench

Next.js debugging console for a FastAPI + LangGraph Agent backend. The app starts in mock mode, so the workbench is usable before the backend is ready.

## Commands

```bash
npm install
npm run dev
npm run test:run
npm run build
```

## Modes

Mock mode is the default:

```env
NEXT_PUBLIC_AGENT_API_MODE=mock
```

Real mode sends browser requests to the Next.js proxy route at `POST /api/agent/run`, which forwards them to FastAPI:

```env
NEXT_PUBLIC_AGENT_API_MODE=real
AGENT_API_BASE_URL=http://localhost:8000
```

The expected FastAPI endpoint is:

```text
POST /agent/run
```

The response should include the run id, status, prompt, nodes, trace events, tool calls, vector matches, request JSON, response JSON, and final answer.
