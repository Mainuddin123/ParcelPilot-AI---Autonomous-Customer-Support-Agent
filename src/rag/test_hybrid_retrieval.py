
from src.rag.retriever import Retriever

retriever = Retriever()

test_queries = [
    "What is the cancellation policy?",
    "How can a customer claim service credit?",
    "What is the escalation SLA?",
    "What happens during a failed pickup?",
    "What are the customer agreement terms?",
]

for query in test_queries:
    print("\n" + "=" * 65)
    print("QUERY:", query)

    results = retriever.retrieve(
        query,
        top_k=3
    )

    print("RESULT COUNT:", len(results))

    for rank, result in enumerate(results, start=1):
        print(f"\nRank: {rank}")
        print("Source:", result.get("source"))
        print("Page:", result.get("page"))
        print("RRF Score:", result.get("rrf_score"))
        print("Text:", result.get("text", "")[:200])

    print("\nCITATIONS:", retriever.get_citations(results))

print("\nHybrid retrieval evaluation completed.")
