from pathlib import Path

import chromadb

from app.errors import NonRetryableIngestionError, RetryableIngestionError


class ChromaVectorStore:
    def __init__(self, persist_dir: Path) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_dir))

    def ensure_collection(self, name: str) -> None:
        self.client.get_or_create_collection(name)

    def list_collections(self) -> list[str]:
        collections = self.client.list_collections()
        names = [collection if isinstance(collection, str) else collection.name for collection in collections]
        return sorted(names)

    def add_chunks(
        self,
        collection: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        if len({len(ids), len(texts), len(embeddings), len(metadatas)}) != 1:
            raise NonRetryableIngestionError("Chroma chunk ids, texts, embeddings, and metadatas must have the same length.")

        if len(ids) != len(set(ids)):
            raise NonRetryableIngestionError("Chroma chunk ids must not contain duplicate values.")

        if any(not isinstance(metadata, dict) for metadata in metadatas):
            raise NonRetryableIngestionError("Chroma chunk metadata entries must be dictionaries.")

        if any(not isinstance(embedding, list) for embedding in embeddings):
            raise NonRetryableIngestionError("Chroma chunk embedding entries must be lists.")

        try:
            target = self.client.get_or_create_collection(collection)
            target.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        except Exception as exc:
            raise RetryableIngestionError(f"Chroma write failed: {exc}") from exc
