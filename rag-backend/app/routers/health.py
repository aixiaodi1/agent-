from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.dependencies import get_embedder, get_queue_client, get_repository, get_vector_store
from app.infrastructure.embeddings.base import EmbeddingProvider
from app.infrastructure.queue.base import QueueClient
from app.infrastructure.repositories.base import Repository
from app.infrastructure.vectorstores.base import VectorStore


router = APIRouter(tags=["health"])


def _run_check(check: Callable[[], object]) -> dict:
    try:
        check()
    except Exception:
        return {"status": "error", "error": "check_failed"}
    return {"status": "ok"}


def _check_redis(queue_client: QueueClient) -> None:
    if hasattr(queue_client, "ping"):
        queue_client.ping()
        return

    redis_client = getattr(queue_client, "redis", None)
    if redis_client is not None and hasattr(redis_client, "ping"):
        redis_client.ping()


def _check_embedding_provider(embedder: EmbeddingProvider) -> None:
    if not callable(getattr(embedder, "embed_texts", None)):
        raise RuntimeError("embedding provider unavailable")


@router.get("/health")
def health(
    repository: Repository = Depends(get_repository),
    queue_client: QueueClient = Depends(get_queue_client),
    vector_store: VectorStore = Depends(get_vector_store),
    embedder: EmbeddingProvider = Depends(get_embedder),
) -> dict:
    checks = {
        "api": {"status": "ok"},
        "redis": _run_check(lambda: _check_redis(queue_client)),
        "chroma": _run_check(lambda: vector_store.list_collections()),
        "embedding_api": _run_check(lambda: _check_embedding_provider(embedder)),
        "sqlite": _run_check(repository.initialize),
    }
    overall_status = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
    return {"status": overall_status, "checks": checks}
