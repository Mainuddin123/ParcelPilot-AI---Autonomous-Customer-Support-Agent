
import re
import threading
import heapq

from rank_bm25 import BM25Okapi

from src.rag.vector_store import VectorStore
from src.rag.reranker import CrossEncoderReranker
from src.tracing import traced


class Retriever:
    """Hybrid ChromaDB + BM25 retrieval with RRF and reranking."""

    EXCLUDED = {
        "deprecated",
        "deprecated_policy",
        "obsolete",
        "archived",
    }

    SOURCE_PRIORITY = {
        "customer_agreement": 4,
        "current_sop": 3,
        "current_policy": 2,
        "product_operations": 1,
        "general_document": 1,
    }

    @traced(name="parcelpilot.retriever_and_bm25_initialization")
    def __init__(
        self,
        candidate_k=20,
        rrf_k=60,
        enable_reranking=True,
    ):
        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero.")

        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than zero.")

        self.vector_store = VectorStore()
        self.vector_store.load()

        self.candidate_k = candidate_k
        self.rrf_k = rrf_k

        self.reranker = None
        self.enable_reranking = enable_reranking
        self._reranker_lock = threading.Lock()

        self._chunks = list(self.vector_store.chunks)

        tokenized = [
            self._tokenize(chunk.get("text", ""))
            for chunk in self._chunks
        ]

        self.bm25 = BM25Okapi(tokenized) if tokenized else None

    @staticmethod
    def _tokenize(text):
        return re.findall(r"[a-z0-9]+", str(text).lower())

    def _allowed(self, chunk, account_id):
        """Apply document lifecycle and account-level filtering."""

        source_type = str(
            chunk.get("source_type", "")
        ).lower()

        status = str(
            chunk.get("status", "current")
        ).lower()

        if source_type in self.EXCLUDED or status in self.EXCLUDED:
            return False

        if source_type == "customer_agreement":
            return (
                bool(account_id)
                and chunk.get("account_id") == account_id
            )

        return True

    @traced(name="parcelpilot.bm25_search")
    def _bm25_search(self, query, account_id):
        """Retrieve top BM25 candidates without sorting every score."""

        if self.bm25 is None or not query.strip():
            return []

        scores = self.bm25.get_scores(
            self._tokenize(query)
        )

        top_indices = heapq.nlargest(
            self.candidate_k,
            range(len(scores)),
            key=lambda index: float(scores[index]),
        )

        results = []

        for index in top_indices:
            chunk = self._chunks[index]

            if not self._allowed(chunk, account_id):
                continue

            item = dict(chunk)
            item["bm25_score"] = float(scores[index])
            results.append(item)

        return results

    @traced(name="parcelpilot.hybrid_retrieval")
    def retrieve(self, query, account_id=None, top_k=5):

        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        if not query.strip() or top_k <= 0:
            return []

        # 1. Dense retrieval.
        dense = self.vector_store.search(
            query=query,
            top_k=self.candidate_k,
            account_id=account_id,
        )

        dense = [
            document
            for document in dense
            if self._allowed(document, account_id)
        ]

        # 2. BM25 retrieval.
        lexical = self._bm25_search(
            query,
            account_id,
        )

        # 3. Reciprocal Rank Fusion.
        fused = {}

        for ranking in (dense, lexical):
            for rank, document in enumerate(ranking, start=1):

                key = (
                    document.get("source"),
                    document.get("page"),
                    document.get("text"),
                )

                if key not in fused:
                    fused[key] = dict(document)
                    fused[key]["rrf_score"] = 0.0

                fused[key]["rrf_score"] += (
                    1.0 / (self.rrf_k + rank)
                )

        candidates = list(fused.values())

        # 4. Source authority priority.
        for document in candidates:

            priority = self.SOURCE_PRIORITY.get(
                str(document.get("source_type", "")).lower(),
                0,
            )

            document["rrf_score"] += priority * 0.0001

        candidates.sort(
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        # 5. Lazy Cross-Encoder initialization.
        if self.enable_reranking and self.reranker is None:

            with self._reranker_lock:

                if self.enable_reranking and self.reranker is None:

                    try:
                        self.reranker = CrossEncoderReranker()

                    except Exception as error:
                        print(
                            "Reranker unavailable; "
                            f"using RRF ranking only: {error}"
                        )

                        self.enable_reranking = False

        # 6. Cross-Encoder reranking.
        if self.enable_reranking and self.reranker is not None:

            try:
                return self.reranker.rerank(
                    query,
                    candidates,
                    top_k=top_k,
                )

            except Exception as error:

                print(
                    "Reranker prediction failed; "
                    f"using RRF ranking only: {error}"
                )

                self.reranker = None
                self.enable_reranking = False

        # 7. RRF fallback.
        return candidates[:top_k]

    @traced(name="parcelpilot.context_formatting")
    def format_context(self, results):

        if not results:
            return "No relevant documents found."

        parts = []

        for index, result in enumerate(results, start=1):

            parts.append(
                f"[SOURCE {index}]\n"
                f"Document: {result.get('source', 'Unknown')}\n"
                f"Page: {result.get('page', 'Unknown')}\n"
                f"Source Type: "
                f"{result.get('source_type', 'general_document')}\n\n"
                f"{result.get('text', '')}"
            )

        return "\n\n".join(parts)

    def get_citations(self, results):

        citations = []
        seen = set()

        for result in results:

            citation = {
                "source": result.get("source", "Unknown"),
                "page": result.get("page", "Unknown"),
                "source_type": result.get(
                    "source_type",
                    "general_document",
                ),
            }

            key = (
                citation["source"],
                citation["page"],
            )

            if key not in seen:
                citations.append(citation)
                seen.add(key)

        citations.sort(
            key=lambda item: self.SOURCE_PRIORITY.get(
                str(item["source_type"]).lower(),
                0,
            ),
            reverse=True,
        )

        return citations
