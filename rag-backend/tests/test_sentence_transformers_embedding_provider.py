import pytest

from app.errors import NonRetryableIngestionError
from app.infrastructure.embeddings.sentence_transformers import SentenceTransformersEmbeddingProvider


class FakeLangChainEmbeddings:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.documents: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents.append(texts)
        return [[float(index), 0.5] for index, _text in enumerate(texts)]


class BadLangChainEmbeddings:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, "bad"] for _text in texts]


def test_sentence_transformers_provider_embeds_documents_in_batches() -> None:
    provider = SentenceTransformersEmbeddingProvider(
        model_name="shibing624/text2vec-base-chinese",
        batch_size=2,
        embeddings_cls=FakeLangChainEmbeddings,
    )

    assert provider.embed_texts(["one", "two", "three"]) == [[0.0, 0.5], [1.0, 0.5], [0.0, 0.5]]
    assert provider._embeddings.model_name == "shibing624/text2vec-base-chinese"
    assert provider._embeddings.documents == [["one", "two"], ["three"]]


def test_sentence_transformers_provider_rejects_invalid_vectors() -> None:
    provider = SentenceTransformersEmbeddingProvider(
        model_name="local-model",
        batch_size=2,
        embeddings_cls=BadLangChainEmbeddings,
    )

    with pytest.raises(NonRetryableIngestionError, match="finite numeric"):
        provider.embed_texts(["hello"])
