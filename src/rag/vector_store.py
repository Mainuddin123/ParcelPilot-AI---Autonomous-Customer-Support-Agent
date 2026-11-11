import pickle
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import STORAGE_DIR
from src.tracing import traced


@lru_cache(maxsize=1)
def get_embedding_model():
    """Reuse the embedding model across chat sessions in this process."""
    return SentenceTransformer("all-MiniLM-L6-v2")


class VectorStore:

    EXCLUDED_STATUSES = {
        "deprecated",
        "obsolete",
        "archived"
    }

    def __init__(self):

        self.model = get_embedding_model()

        self.index = None
        self.chunks = []

        self.index_path = (
            STORAGE_DIR / "faiss_index.bin"
        )

        self.chunks_path = (
            STORAGE_DIR / "chunks.pkl"
        )

    def build(self, chunks):
        """
        Convert document chunks into embeddings
        and build the FAISS vector index.
        """

        self.chunks = chunks

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        embeddings = np.array(
            embeddings,
            dtype="float32"
        )

        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(embeddings)

        STORAGE_DIR.mkdir(
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(self.index_path)
        )

        with open(
            self.chunks_path,
            "wb"
        ) as file:

            pickle.dump(
                self.chunks,
                file
            )

    def load(self):
        """
        Load the saved FAISS index
        and document chunks.
        """

        self.index = faiss.read_index(
            str(self.index_path)
        )

        with open(
            self.chunks_path,
            "rb"
        ) as file:

            self.chunks = pickle.load(
                file
            )

    @traced(name="parcelpilot.faiss_dense_search")
    def search(
        self,
        query,
        top_k=5,
        account_id=None,
        include_deprecated=False
    ):
        """Search only the candidates needed, expanding when access filters apply."""
        if self.index is None:
            raise ValueError("Vector store is not loaded.")
        if not self.chunks or top_k <= 0:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        )
        query_embedding = np.asarray(query_embedding, dtype="float32")
        faiss.normalize_L2(query_embedding)

        # Avoid scanning the full index on every request. Expand only when
        # account/status filters leave too few eligible candidates.
        search_k = min(max(top_k * 4, top_k), len(self.chunks))
        results = []
        while True:
            scores, indices = self.index.search(query_embedding, search_k)
            results = []
            for score, chunk_idx in zip(scores[0], indices[0]):
                if chunk_idx < 0:
                    continue
                chunk = self.chunks[int(chunk_idx)]
                status = str(chunk.get("status", "current")).lower()
                source_type = str(chunk.get("source_type", "")).lower()
                if not include_deprecated and (
                    status in self.EXCLUDED_STATUSES
                    or source_type in self.EXCLUDED_STATUSES
                ):
                    continue
                if source_type == "customer_agreement":
                    if not account_id or chunk.get("account_id") != account_id:
                        continue
                results.append({**chunk, "score": float(score)})
                if len(results) >= top_k:
                    break

            if len(results) >= top_k or search_k >= len(self.chunks):
                break
            search_k = min(search_k * 2, len(self.chunks))

        return results[:top_k]