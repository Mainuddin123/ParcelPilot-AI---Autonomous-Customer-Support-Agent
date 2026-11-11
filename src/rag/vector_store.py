"""Persistent ChromaDB vector store for ParcelPilot AI.

The public interface intentionally matches the retriever's expected contract:
    VectorStore().load()
    VectorStore.search(query, top_k=..., account_id=...)

Chroma stores cosine distances (lower is better). This module converts them
to similarity scores (1 - distance) to preserve the previous score convention.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import STORAGE_DIR
from src.tracing import traced


CHROMA_DIR = Path(STORAGE_DIR) / "chroma_db"
COLLECTION_NAME = "parcelpilot_documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 128
INSERT_BATCH_SIZE = 500


@traced(name="parcelpilot.embedding_model_load")
@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once per process."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def _safe_metadata(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Keep only ChromaDB-supported, non-null metadata values."""
    metadata: dict[str, str | int | float | bool] = {}
    for key, value in chunk.items():
        if key == "text" or value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
    return metadata


class VectorStore:
    """ChromaDB-backed dense vector store."""

    EXCLUDED_STATUSES = {"deprecated", "obsolete", "archived"}

    def __init__(self) -> None:
        self.model = get_embedding_model()
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = None
        self.chunks: list[dict[str, Any]] = []

    def build(self, chunks: list[dict[str, Any]]) -> None:
        """Create or replace the persistent collection from document chunks."""
        if not chunks:
            raise ValueError("Cannot build ChromaDB from an empty chunk list.")

        texts = [str(chunk.get("text", "")) for chunk in chunks]
        if any(not text.strip() for text in texts):
            raise ValueError("Every chunk must contain non-empty text.")

        # Compute embeddings before replacing the existing collection. This
        # avoids deleting a valid index if embedding generation fails.
        embeddings = self.model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        metadata = [_safe_metadata(chunk) for chunk in chunks]
        ids = [f"chunk-{index:08d}" for index in range(len(chunks))]

        # Replace the collection only after all input data has been prepared.
        try:
            self.client.delete_collection(name=COLLECTION_NAME)
        except Exception as exc:
            # ChromaDB versions expose NotFoundError differently. Ignore only
            # the expected missing-collection case; re-raise other failures.
            not_found = getattr(chromadb.errors, "NotFoundError", ())
            if not_found and isinstance(exc, not_found):
                pass
            elif "does not exist" in str(exc).lower() or "not found" in str(exc).lower():
                pass
            else:
                raise

        self.collection = self.client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        for start in range(0, len(chunks), INSERT_BATCH_SIZE):
            end = start + INSERT_BATCH_SIZE
            self.collection.add(
                ids=ids[start:end],
                embeddings=embeddings[start:end].tolist(),
                documents=texts[start:end],
                metadatas=metadata[start:end],
            )

        self.chunks = [
            {**metadata[index], "text": texts[index]}
            for index in range(len(texts))
        ]
        print(f"ChromaDB indexed {self.collection.count()} chunks.")

    @traced(name="parcelpilot.chroma_collection_load")
    def load(self) -> None:
        """Load an existing persistent ChromaDB collection and its chunks."""
        try:
            collection = self.client.get_collection(name=COLLECTION_NAME)
        except Exception as exc:
            not_found = getattr(chromadb.errors, "NotFoundError", ())
            if not_found and isinstance(exc, not_found):
                raise FileNotFoundError(
                    "ChromaDB collection not found. Run "
                    "'python build_vector_store.py' first."
                ) from exc
            if "does not exist" in str(exc).lower() or "not found" in str(exc).lower():
                raise FileNotFoundError(
                    "ChromaDB collection not found. Run "
                    "'python build_vector_store.py' first."
                ) from exc
            raise

        count = collection.count()
        if count == 0:
            raise ValueError("ChromaDB collection exists but contains no documents.")

        self.collection = collection
        self.chunks = []
        # ChromaDB get() returns records in batches; paginate to avoid relying
        # on a version-specific default result limit.
        page_size = 1000
        for offset in range(0, count, page_size):
            stored = collection.get(
                limit=min(page_size, count - offset),
                offset=offset,
                include=["documents", "metadatas"],
            )
            documents = stored.get("documents") or []
            metadatas = stored.get("metadatas") or []
            for document, metadata in zip(documents, metadatas):
                self.chunks.append({**(metadata or {}), "text": document})

        print(f"Loaded {len(self.chunks)} chunks from ChromaDB.")

    @traced(name="parcelpilot.chroma_dense_search")
    def search(
        self,
        query: str,
        top_k: int = 5,
        account_id: str | None = None,
        include_deprecated: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the best eligible chunks, with account-level filtering."""
        if not isinstance(query, str):
            raise TypeError("query must be a string.")
        if not query.strip() or top_k <= 0:
            return []
        if self.collection is None:
            raise ValueError("VectorStore is not loaded. Call load() or build() first.")

        total = self.collection.count()
        if total == 0:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Start with a bounded candidate pool. Expand only when post-retrieval
        # eligibility filters leave too few results.
        search_k = min(max(top_k * 4, top_k), total)
        while True:
            response = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=search_k,
                include=["documents", "metadatas", "distances"],
            )

            documents = (response.get("documents") or [[]])[0] or []
            metadatas = (response.get("metadatas") or [[]])[0] or []
            distances = (response.get("distances") or [[]])[0] or []

            results: list[dict[str, Any]] = []
            for document, metadata, distance in zip(documents, metadatas, distances):
                chunk = {**(metadata or {}), "text": document}
                status = str(chunk.get("status", "current")).strip().lower()
                source_type = str(chunk.get("source_type", "")).strip().lower()

                if not include_deprecated and (
                    status in self.EXCLUDED_STATUSES
                    or source_type in self.EXCLUDED_STATUSES
                ):
                    continue

                # Customer-specific documents must never be returned without
                # a matching authenticated account identifier.
                if source_type == "customer_agreement":
                    if not account_id or chunk.get("account_id") != account_id:
                        continue

                chunk["score"] = float(1.0 - float(distance))
                results.append(chunk)
                if len(results) >= top_k:
                    break

            if len(results) >= top_k or search_k >= total:
                break
            search_k = min(search_k * 2, total)

        return results[:top_k]
