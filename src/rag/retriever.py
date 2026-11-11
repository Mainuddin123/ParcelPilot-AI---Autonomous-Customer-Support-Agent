import re
from rank_bm25 import BM25Okapi

from src.rag.vector_store import VectorStore
from src.rag.reranker import CrossEncoderReranker
from src.tracing import traced


class Retriever:
    """Dense FAISS + BM25 retrieval, RRF fusion and optional reranking."""

    EXCLUDED = {"deprecated", "deprecated_policy", "obsolete", "archived"}
    SOURCE_PRIORITY = {
        "customer_agreement": 4,
        "current_sop": 3,
        "current_policy": 2,
        "product_operations": 1,
        "general_document": 1,
    }

    def __init__(self, candidate_k=20, rrf_k=60, enable_reranking=True):
        self.vector_store = VectorStore()
        self.vector_store.load()
        self.candidate_k = candidate_k
        self.rrf_k = rrf_k
        self.reranker = None
        self.enable_reranking = enable_reranking
        self._chunks = list(self.vector_store.chunks)
        tokenized = [self._tokenize(c.get("text", "")) for c in self._chunks]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

    @staticmethod
    def _tokenize(text):
        return re.findall(r"[a-z0-9]+", str(text).lower())

    def _allowed(self, chunk, account_id):
        source_type = str(chunk.get("source_type", "")).lower()
        status = str(chunk.get("status", "current")).lower()
        if source_type in self.EXCLUDED or status in self.EXCLUDED:
            return False
        if source_type == "customer_agreement":
            return bool(account_id) and chunk.get("account_id") == account_id
        return True

    def _bm25_search(self, query, account_id):
        if self.bm25 is None:
            return []
        scores = self.bm25.get_scores(self._tokenize(query))
        indices = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        results = []
        for idx in indices:
            chunk = self._chunks[idx]
            if not self._allowed(chunk, account_id):
                continue
            item = dict(chunk)
            item["bm25_score"] = float(scores[idx])
            results.append(item)
            if len(results) >= self.candidate_k:
                break
        return results

    @traced("parcelpilot.hybrid_retrieval")
    def retrieve(self, query, account_id=None, top_k=5):
        dense = self.vector_store.search(
            query=query, top_k=self.candidate_k, account_id=account_id
        )
        lexical = self._bm25_search(query, account_id)

        fused = {}
        for ranking in (dense, lexical):
            for rank, doc in enumerate(ranking, start=1):
                key = (doc.get("source"), doc.get("page"), doc.get("text"))
                if key not in fused:
                    fused[key] = dict(doc)
                    fused[key]["rrf_score"] = 0.0
                fused[key]["rrf_score"] += 1.0 / (self.rrf_k + rank)

        candidates = list(fused.values())
        for doc in candidates:
            priority = self.SOURCE_PRIORITY.get(str(doc.get("source_type", "")).lower(), 0)
            doc["rrf_score"] += priority * 0.0001
        candidates.sort(key=lambda item: item["rrf_score"], reverse=True)

        if self.enable_reranking and self.reranker is None:
            try:
                self.reranker = CrossEncoderReranker()
            except Exception as error:
                # Keep hybrid retrieval available if model download/loading fails.
                print(f"Reranker unavailable; using RRF ranking only: {error}")
                self.enable_reranking = False

        if self.reranker is not None:
            return self.reranker.rerank(query, candidates, top_k=top_k)
        return candidates[:top_k]

    def format_context(self, results):
        if not results:
            return "No relevant documents found."
        parts = []
        for i, result in enumerate(results, start=1):
            parts.append(
                f"[SOURCE {i}]\nDocument: {result.get('source', 'Unknown')}\n"
                f"Page: {result.get('page', 'Unknown')}\n"
                f"Source Type: {result.get('source_type', 'general_document')}\n\n"
                f"{result.get('text', '')}"
            )
        return "\n\n".join(parts)

    def get_citations(self, results):
        citations, seen = [], set()
        for result in results:
            citation = {
                "source": result.get("source", "Unknown"),
                "page": result.get("page", "Unknown"),
                "source_type": result.get("source_type", "general_document"),
            }
            key = (citation["source"], citation["page"])
            if key not in seen:
                citations.append(citation)
                seen.add(key)
        citations.sort(
            key=lambda item: self.SOURCE_PRIORITY.get(item["source_type"], 0),
            reverse=True,
        )
        return citations
