from functools import lru_cache
from src.tracing import traced


@traced(name="parcelpilot.cross_encoder_model_load")
@lru_cache(maxsize=1)
def _load_cross_encoder(model_name):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


class CrossEncoderReranker:
    """Rerank query-document pairs using a cross-encoder model.

    The model is loaded lazily so optional reranking dependency/model
    failures do not prevent the base retrieval pipeline from starting.
    """

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = _load_cross_encoder(model_name)

    @traced(name="parcelpilot.cross_encoder_reranking")
    def rerank(self, query, documents, top_k=5):
        if not documents:
            return []
        pairs = [(query, str(doc.get("text", ""))) for doc in documents]
        scores = self.model.predict(pairs, batch_size=32, show_progress_bar=False)
        ranked = []
        for doc, score in zip(documents, scores):
            item = dict(doc)
            item["rerank_score"] = float(score)
            ranked.append(item)
        ranked.sort(key=lambda item: item["rerank_score"], reverse=True)
        return ranked[:top_k]
