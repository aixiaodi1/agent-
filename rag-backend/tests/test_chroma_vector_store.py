import shutil
import time
from pathlib import Path

import pytest

from app.errors import NonRetryableIngestionError, RetryableIngestionError
from app.infrastructure.vectorstores.chroma_store import ChromaVectorStore


def make_store_with_client(client) -> ChromaVectorStore:
    store = ChromaVectorStore.__new__(ChromaVectorStore)
    store.client = client
    store._closed = False
    return store


@pytest.fixture
def store(tmp_path: Path):
    store = ChromaVectorStore(tmp_path / "chroma")
    try:
        yield store
    finally:
        store.close()


def test_chroma_store_adds_chunks_with_metadata(store: ChromaVectorStore) -> None:
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


def test_chroma_store_lists_collection_names_sorted(store: ChromaVectorStore) -> None:
    store.ensure_collection("zeta")
    store.ensure_collection("alpha")

    assert store.list_collections() == ["alpha", "zeta"]


def test_chroma_store_lists_legacy_string_collection_names_sorted() -> None:
    class LegacyClient:
        def list_collections(self) -> list[str]:
            return ["z", "a"]

    store = make_store_with_client(LegacyClient())

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
    ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    match: str,
) -> None:
    class UnexpectedClient:
        def get_or_create_collection(self, name: str) -> None:
            raise AssertionError("validation should run before Chroma writes")

    store = make_store_with_client(UnexpectedClient())

    with pytest.raises(NonRetryableIngestionError, match=match):
        store.add_chunks(
            collection="docs",
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def test_chroma_store_wraps_write_errors() -> None:
    class BrokenCollection:
        def add(self, **kwargs) -> None:
            raise RuntimeError("disk unavailable")

    class FakeClient:
        def get_or_create_collection(self, name: str) -> BrokenCollection:
            return BrokenCollection()

    store = make_store_with_client(FakeClient())

    with pytest.raises(RetryableIngestionError, match="Chroma write failed"):
        store.add_chunks(
            collection="docs",
            ids=["doc_1:0"],
            texts=["hello chroma"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source_file": "guide.md"}],
        )


def test_chroma_store_close_uses_client_close_once() -> None:
    class ClosableClient:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

    client = ClosableClient()
    store = make_store_with_client(client)

    store.close()
    store.close()

    assert client.close_calls == 1


def test_chroma_store_close_falls_back_to_system_stop_once() -> None:
    class System:
        def __init__(self) -> None:
            self.stop_calls = 0

        def stop(self) -> None:
            self.stop_calls += 1

    class ClientWithSystem:
        def __init__(self) -> None:
            self._system = System()

    client = ClientWithSystem()
    store = make_store_with_client(client)

    store.close()
    store.close()

    assert client._system.stop_calls == 1


def test_chroma_store_close_allows_chroma_directory_cleanup(tmp_path: Path) -> None:
    chroma_dir = tmp_path / "chroma"
    store = ChromaVectorStore(chroma_dir)
    store.add_chunks(
        collection="docs",
        ids=["doc_1:0"],
        texts=["hello chroma"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"source_file": "guide.md"}],
    )

    store.close()

    destination = tmp_path / "renamed"
    last_error: OSError | None = None
    for _ in range(10):
        try:
            chroma_dir.rename(destination)
            shutil.rmtree(destination)
            last_error = None
            break
        except OSError as exc:
            last_error = exc
            time.sleep(0.1)

    assert last_error is None
