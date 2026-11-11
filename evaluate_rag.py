"""Evaluate retrieval rankings against manually labeled relevant document IDs.

Input JSON format:
[
  {"query": "...", "relevant_ids": ["doc-1"], "retrieved_ids": ["doc-1", "doc-2"]}
]
Do not report benchmark scores until the labels are reviewed.
"""
import json
import math
import sys
from pathlib import Path


def precision_at_k(retrieved, relevant, k):
    top = retrieved[:k]
    return sum(x in relevant for x in top) / k if k else 0.0


def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0
    return sum(x in relevant for x in retrieved[:k]) / len(relevant)


def reciprocal_rank(retrieved, relevant):
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved, relevant, k):
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, item in enumerate(retrieved[:k], start=1)
        if item in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def evaluate(rows, k=5):
    valid = [r for r in rows if r.get("relevant_ids")]
    if not valid:
        raise ValueError("No labeled queries with non-empty relevant_ids were provided.")
    metrics = {"precision_at_k": [], "recall_at_k": [], "mrr": [], "ndcg_at_k": []}
    for row in valid:
        retrieved = row.get("retrieved_ids", [])
        relevant = set(row["relevant_ids"])
        metrics["precision_at_k"].append(precision_at_k(retrieved, relevant, k))
        metrics["recall_at_k"].append(recall_at_k(retrieved, relevant, k))
        metrics["mrr"].append(reciprocal_rank(retrieved, relevant))
        metrics["ndcg_at_k"].append(ndcg_at_k(retrieved, relevant, k))
    return {name: round(sum(values) / len(values), 4) for name, values in metrics.items()}


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "evaluation_dataset.json")
    with path.open(encoding="utf-8") as handle:
        dataset = json.load(handle)
    print(json.dumps(evaluate(dataset), indent=2))
