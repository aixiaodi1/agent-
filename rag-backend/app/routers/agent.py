from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_embedder, get_vector_store
from app.infrastructure.embeddings.base import EmbeddingProvider
from app.infrastructure.vectorstores.base import VectorStore
from app.sanitization import sanitize_error_message


router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    agent_id: str = Field(default="research-agent", alias="agentId")
    thread_id: str | None = Field(default=None, alias="threadId")
    vector_provider: str = Field(default="chroma", alias="vectorProvider")
    collection: str = "default"
    debug: bool = True


@router.post("/run")
def run_agent(
    request: AgentRunRequest,
    embedder: EmbeddingProvider = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
) -> dict:
    started = datetime.now(UTC)
    started_at = started.isoformat()
    timer = perf_counter()

    try:
        query_embedding = embedder.embed_texts([request.prompt])[0]
        raw_matches = vector_store.query_chunks(request.collection, query_embedding, n_results=5)
    except Exception as exc:
        detail = sanitize_error_message(str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Agent retrieval failed: {detail}") from exc

    finished_at = datetime.now(UTC).isoformat()
    latency_ms = int((perf_counter() - timer) * 1000)
    vector_matches = [
        _serialize_vector_match(match, index=index, collection=request.collection)
        for index, match in enumerate(raw_matches)
    ]
    final_answer = _build_retrieval_answer(request.prompt, vector_matches)
    run_id = f"run_{uuid4().hex}"
    request_json = request.model_dump(by_alias=True)

    return {
        "id": run_id,
        "mode": "real",
        "prompt": request.prompt,
        "status": "succeeded",
        "startedAt": started_at,
        "finishedAt": finished_at,
        "latencyMs": latency_ms,
        "nodes": [
            {
                "id": "receive_question",
                "label": "Receive question",
                "status": "succeeded",
                "startedAt": started_at,
                "stateSummary": "Received the prompt from the Next.js debug console.",
            },
            {
                "id": "retrieve_context",
                "label": "Retrieve Chroma context",
                "status": "succeeded",
                "startedAt": started_at,
                "finishedAt": finished_at,
                "durationMs": latency_ms,
                "stateSummary": f"Retrieved {len(vector_matches)} chunks from Chroma collection '{request.collection}'.",
            },
            {
                "id": "generate_answer",
                "label": "Build debug answer",
                "status": "succeeded",
                "finishedAt": finished_at,
                "durationMs": 0,
                "stateSummary": "Returned a retrieval-focused debug answer.",
            },
        ],
        "events": [
            {
                "id": f"{run_id}_evt_receive",
                "nodeId": "receive_question",
                "type": "node_start",
                "timestamp": started_at,
                "title": "Prompt received",
                "detail": request.prompt,
                "payload": {"prompt": request.prompt},
            },
            {
                "id": f"{run_id}_evt_retrieve",
                "nodeId": "retrieve_context",
                "type": "retrieval",
                "timestamp": finished_at,
                "title": "Chroma retrieval",
                "detail": f"Retrieved {len(vector_matches)} chunks from {request.collection}.",
                "payload": {"vectorMatches": vector_matches},
            },
            {
                "id": f"{run_id}_evt_answer",
                "nodeId": "generate_answer",
                "type": "final_answer",
                "timestamp": finished_at,
                "title": "Debug answer",
                "detail": final_answer,
                "payload": {"finalAnswer": final_answer},
            },
        ],
        "toolCalls": [],
        "vectorMatches": vector_matches,
        "requestJson": request_json,
        "responseJson": {
            "collection": request.collection,
            "vectorProvider": "chroma",
            "matchCount": len(vector_matches),
        },
        "finalAnswer": final_answer,
    }


def _serialize_vector_match(match: dict, index: int, collection: str) -> dict:
    metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
    distance = match.get("distance")
    score = None if distance is None else max(0.0, 1.0 - float(distance))
    title = metadata.get("section_title") or metadata.get("clause_title") or metadata.get("source_file") or f"Chroma chunk {index + 1}"
    return {
        "id": str(match.get("id") or f"vec_{index + 1}"),
        "nodeId": "retrieve_context",
        "provider": "chroma",
        "collection": collection,
        "score": score,
        "title": str(title),
        "contentPreview": str(match.get("document") or "")[:600],
        "metadata": metadata,
    }


def _build_retrieval_answer(prompt: str, vector_matches: list[dict]) -> str:
    if not vector_matches:
        return f"No Chroma chunks were retrieved for: {prompt}"

    previews = "\n".join(
        f"{index + 1}. {match['title']}: {match['contentPreview'][:120]}"
        for index, match in enumerate(vector_matches[:3])
    )
    return f"Retrieved {len(vector_matches)} Chroma chunks for the prompt. Top context:\n{previews}"
