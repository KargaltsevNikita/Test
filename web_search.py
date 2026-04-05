"""RAG retriever and vector store helpers."""

from __future__ import annotations

from typing import Any

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.config import Settings


class KBRetriever:
    """Knowledge base retrieval over a local Qdrant collection."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )

        # Local mode is convenient for development and small knowledge bases.
        self.client = QdrantClient(path=str(settings.qdrant_dir))
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=settings.qdrant_collection,
            embedding=self.embeddings,
        )

    def similarity_search(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        """Return normalized docs with scores for downstream reasoning."""
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        normalized: list[dict[str, Any]] = []
        for doc, score in docs_and_scores:
            normalized.append(
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "title": doc.metadata.get("title", "KB document"),
                    "url": doc.metadata.get("url"),
                    "snippet": doc.page_content[:250],
                    "source_type": "kb",
                }
            )
        return normalized

    def has_confident_answer(self, docs: list[dict[str, Any]]) -> bool:
        """Simple confidence heuristic.

        Depending on your embedding/vector store, score semantics may differ.
        Adjust this threshold against a validation set.
        """
        if not docs:
            return False
        best_score = docs[0]["score"]
        return best_score <= self.settings.kb_min_score
