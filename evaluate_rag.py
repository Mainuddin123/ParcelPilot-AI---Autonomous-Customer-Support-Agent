"""Run labeled retrieval evaluation against the live ParcelPilot retriever.

Dataset entries require query and relevant_ids. Document IDs use source:page.
Metrics are computed from actual hybrid retrieval output, not placeholders.
"""
import json
import math
import sys
from pathlib import Path

from src.rag.retriever import Retriever


def precision_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / k if k else 0.0


def recall_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / len(relevant) if relevant else 0.0


def reciprocal_rank(retrieved, relevant):
    for rank, item in enumerate(retrieved, 1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved, relevant, k):
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, item in enumerate(retrieved[:k], 1)
        if item in relevant
    )
    ideal = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    return dcg / idcg if idcg else 0.0


def evaluate(dataset, retriever, k=5):
    metrics = {name: [] for name in ("precision_at_k", "recall_at_k", "mrr", "ndcg_at_k")}
    for row in dataset:
        relevant = set(row["relevant_ids"])
        docs = retriever.retrieve(
            row["query"], account_id=row.get("account_id"), top_k=k
        )
        retrieved = [
            f'{doc.get("source", "unknown")}:{doc.get("page", "unknown")}'
            for doc in docs
        ]
        metrics["precision_at_k"].append(precision_at_k(retrieved, relevant, k))
        metrics["recall_at_k"].append(recall_at_k(retrieved, relevant, k))
        metrics["mrr"].append(reciprocal_rank(retrieved, relevant))
        metrics["ndcg_at_k"].append(ndcg_at_k(retrieved, relevant, k))
        print(f'Query: {row["query"]}')
        print(f"Retrieved: {retrieved}")
        print(f"Relevant:  {sorted(relevant)}\n")
    return {name: round(sum(values) / len(values), 4) for name, values in metrics.items()}


if __name__ == "__main__":
    dataset_path = Path(sys.argv[1] if len(sys.argv) > 1 else "evaluation_dataset.json")
    with dataset_path.open(encoding="utf-8") as file:
        dataset = json.load(file)
    if not dataset or any(not row.get("relevant_ids") for row in dataset):
        raise ValueError("Add reviewed relevant_ids for every query in evaluation_dataset.json.")
    retriever = Retriever()
    print("Aggregate metrics:")
    print(json.dumps(evaluate(dataset, retriever), indent=2))
