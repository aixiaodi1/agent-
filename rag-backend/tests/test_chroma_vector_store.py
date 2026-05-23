from pathlib import Path

import pytest

from app.errors import RetryableIngestionError
from app.infrastructure.vectorstores.chroma_store import ChromaVectorStore


def test_chroma_store_adds_chunks_with_metadata(tmp_path: Path) -> None:
    store = ChromaVectorStore(tmp_path / "chroma")
    store.ensure_collection("docs")
    store.add_chunks(
        collection="docs",
        ids=["doc_1:0"],
        texts=["hello chroma"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[
            {
                "document_id": "doc_1",
                "filename": "guide.md",
                "source_file": "guide.md",
                "collection": "docs",
                "chunk_index": 0,
                "upload_time": "2026-05-24T10:00:00+08:00",
                "source": "upload",
                "content_hash": "abc",
            }
        ],
    )

    collection = store.client.get_collection("docs")
    result = collection.get(ids=["doc_1:0"], include=["documents", "metadatas"])

    assert result["documents"] == ["hello chroma"]
    assert result["metadatas"][0]["source_file"] == "guide.md"
    assert result["metadatas"][0]["chunk_index"] == 0


def test_chroma_store_lists_collection_names_sorted(tmp_path: Path) -> None:
    store = ChromaVectorStore(tmp_path / "chroma")
    store.ensure_collection("zeta")
    store.ensure_collection("alpha")

    assert store.list_collections() == ["alpha", "zeta"]


def test_chroma_store_wraps_write_errors(monkeypatch, tmp_path: Path) -> None:
    class BrokenCollection:
        def add(self, **kwargs) -> None:
            raise RuntimeError("disk unavailable")

    class FakeClient:
        def get_or_create_collection(self, name: str) -> BrokenCollection:
            return BrokenCollection()

    store = ChromaVectorStore(tmp_path / "chroma")
    monkeypatch.setattr(store, "client", FakeClient())

    with pytest.raises(RetryableIngestionError, match="Chroma write failed"):
        store.add_chunks(
            collection="docs",
            ids=["doc_1:0"],
            texts=["hello chroma"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source_file": "guide.md"}],
        )
