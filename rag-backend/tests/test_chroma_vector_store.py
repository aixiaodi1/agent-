from pathlib import Path

import pytest

from app.errors import NonRetryableIngestionError, RetryableIngestionError
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


def test_chroma_store_lists_legacy_string_collection_names_sorted(monkeypatch, tmp_path: Path) -> None:
    class LegacyClient:
        def list_collections(self) -> list[str]:
            return ["z", "a"]

    store = ChromaVectorStore(tmp_path / "chroma")
    monkeypatch.setattr(store, "client", LegacyClient())

    assert store.list_collections() == ["a", "z"]


@pytest.mark.parametrize(
    ("ids", "texts", "embeddings", "metadatas", "match"),
    [
        (["doc_1:0"], ["hello"], [[0.1]], [{"source_file": "guide.md"}, {"source_file": "extra.md"}], "same length"),
        (["doc_1:0", "doc_1:0"], ["hello", "again"], [[0.1], [0.2]], [{"source_file": "guide.md"}, {"source_file": "guide.md"}], "duplicate"),
        (["doc_1:0"], ["hello"], [[0.1]], ["guide.md"], "metadata"),
        (["doc_1:0"], ["hello"], [(0.1, 0.2)], [{"source_file": "guide.md"}], "embedding"),
    ],
)
def test_chroma_store_rejects_deterministic_input_errors_before_write(
    monkeypatch,
    tmp_path: Path,
    ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    match: str,
) -> None:
    class UnexpectedClient:
        def get_or_create_collection(self, name: str) -> None:
            raise AssertionError("validation should run before Chroma writes")

    store = ChromaVectorStore(tmp_path / "chroma")
    monkeypatch.setattr(store, "client", UnexpectedClient())

    with pytest.raises(NonRetryableIngestionError, match=match):
        store.add_chunks(
            collection="docs",
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )


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
