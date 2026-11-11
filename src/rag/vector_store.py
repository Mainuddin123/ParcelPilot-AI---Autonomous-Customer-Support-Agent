import pickle
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import STORAGE_DIR


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

    def search(
        self,
        query,
        top_k=5,
        account_id=None,
        include_deprecated=False
    ):
        """
        Search relevant document chunks.

        Rules:
        1. Deprecated, obsolete, and archived documents
           are excluded by default.
        2. Customer agreements are only returned for
           the matching account_id.
        3. Semantic similarity determines relevance.
        """

        if self.index is None:
            raise ValueError(
                "Vector store is not loaded."
            )

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        )

        query_embedding = np.array(
            query_embedding,
            dtype="float32"
        )

        faiss.normalize_L2(
            query_embedding
        )

        # Search all chunks so filtering does not
        # accidentally remove the only relevant results.
        search_k = len(self.chunks)

        scores, indices = self.index.search(
            query_embedding,
            search_k
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index == -1:
                continue

            chunk = self.chunks[index]

            # =====================================
            # EXCLUDE INACTIVE DOCUMENTS
            # =====================================

            status = str(
                chunk.get(
                    "status",
                    "current"
                )
            ).lower()

            if (
                not include_deprecated
                and status in self.EXCLUDED_STATUSES
            ):
                continue

            # =====================================
            # CUSTOMER AGREEMENT ACCESS CONTROL
            # =====================================

            source_type = str(
                chunk.get(
                    "source_type",
                    ""
                )
            ).lower()

            if source_type == "customer_agreement":

                # Do not expose customer agreements
                # without an account context.
                if account_id is None:
                    continue

                # Only return the agreement belonging
                # to the requested account.
                if (
                    chunk.get("account_id")
                    != account_id
                ):
                    continue

            results.append({
                **chunk,
                "score": float(score)
            })

        # =========================================
        # SEMANTIC RELEVANCE RANKING
        # =========================================

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:top_k]