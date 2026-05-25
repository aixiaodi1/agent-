import os
from collections.abc import Callable
from functools import lru_cache
from math import isfinite
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None


class RerankRequest(BaseModel):
    query: str
    documents: list[str] = Field(min_length=1)
    model: str | None = None
    top_k: int | None = Field(default=None, ge=1)


class LazyModel:
    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._model: Any | None = None

    def get(self) -> Any:
        if self._model is None:
            self._model = self._factory()
        return self._model


def create_model_api_app(
    embedding_model_factory: Callable[[], Any] | None = None,
    rerank_model_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
    rerank_model_name = os.getenv("RERANK_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    embedding_model = LazyModel(embedding_model_factory or _sentence_transformer_factory(embedding_model_name))
    rerank_model = LazyModel(rerank_model_factory or _cross_encoder_factory(rerank_model_name))

    app = FastAPI(title="Local RAG Model API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "embedding_model": embedding_model_name,
            "rerank_model": rerank_model_name,
        }

    @app.post("/v1/embeddings")
    def create_embeddings(request: EmbeddingRequest) -> dict:
        texts = [request.input] if isinstance(request.input, str) else request.input
        if not texts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="input must not be empty")

        model = embedding_model.get()
        try:
            raw_embeddings = model.encode(texts, normalize_embeddings=True)
        except TypeError:
            raw_embeddings = model.encode(texts)

        embeddings = [_coerce_vector(vector) for vector in raw_embeddings]
        response_model = request.model or embedding_model_name
        return {
            "object": "list",
            "model": response_model,
            "embeddings": embeddings,
            "data": [
                {
                    "object": "embedding",
                    "index": index,
                    "embedding": embedding,
                }
                for index, embedding in enumerate(embeddings)
            ],
        }

    @app.post("/v1/rerank")
    def rerank(request: RerankRequest) -> dict:
        model = rerank_model.get()
        pairs = [(request.query, document) for document in request.documents]
        raw_scores = model.predict(pairs)
        scores = [float(score) for score in raw_scores]
        ranked = sorted(
            (
                {
                    "index": index,
                    "document": document,
                    "score": score,
                }
                for index, (document, score) in enumerate(zip(request.documents, scores, strict=True))
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        top_k = request.top_k or len(ranked)
        return {
            "model": request.model or rerank_model_name,
            "results": ranked[:top_k],
        }

    return app


def _sentence_transformer_factory(model_name: str) -> Callable[[], Any]:
    def load_model() -> Any:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(model_name)

    return load_model


def _cross_encoder_factory(model_name: str) -> Callable[[], Any]:
    def load_model() -> Any:
        from sentence_transformers import CrossEncoder

        return CrossEncoder(model_name)

    return load_model


def _coerce_vector(vector: object) -> list[float]:
    if callable(getattr(vector, "tolist", None)):
        vector = vector.tolist()

    if not isinstance(vector, list) or not vector:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="model returned an invalid vector")

    values = [float(value) for value in vector]
    if any(isinstance(value, bool) or not isfinite(value) for value in values):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="model returned an invalid vector")
    return values


@lru_cache
def get_app() -> FastAPI:
    return create_model_api_app()


app = get_app()
