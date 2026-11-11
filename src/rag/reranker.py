class CrossEncoderReranker:
    """Rerank query-document pairs using a cross-encoder model.

    The model is loaded lazily so optional reranking dependency/model
    failures do not prevent the base retrieval pipeline from starting.
    """

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(self, query, documents, top_k=5):
        if not documents:
            return []
        pairs = [(query, str(doc.get("text", ""))) for doc in documents]
        scores = self.model.predict(pairs, show_progress_bar=False)
        ranked = []
        for doc, score in zip(documents, scores):
            item = dict(doc)
            item["rerank_score"] = float(score)
            ranked.append(item)
        ranked.sort(key=lambda item: item["rerank_score"], reverse=True)
        return ranked[:top_k]
