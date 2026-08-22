from src.rag.vector_store import VectorStore


class Retriever:

    # Higher number = higher authority
    SOURCE_PRIORITY = {
        "customer_agreement": 4,
        "current_sop": 3,
        "current_policy": 2,
        "general_document": 1
    }

    # Documents with these types/statuses must not be used
    EXCLUDED_SOURCE_TYPES = {
        "deprecated",
        "obsolete",
        "archived"
    }

    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.load()

    def retrieve(
        self,
        query: str,
        account_id: str = None,
        top_k: int = 5
    ):
        """
        Retrieve relevant and authoritative document chunks.

        Priority:
        1. Customer agreement for the account
        2. Current SOP
        3. Current policy
        4. General documents

        Deprecated, obsolete, and archived documents
        are excluded.
        """

        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            account_id=account_id
        )

        # =========================================
        # EXCLUDE DEPRECATED / OBSOLETE DOCUMENTS
        # =========================================

        valid_results = []

        for result in results:

            source_type = str(
                result.get(
                    "source_type",
                    ""
                )
            ).lower()

            status = str(
                result.get(
                    "status",
                    ""
                )
            ).lower()

            if source_type in self.EXCLUDED_SOURCE_TYPES:
                continue

            if status in self.EXCLUDED_SOURCE_TYPES:
                continue

            valid_results.append(
                result
            )

        # =========================================
        # SOURCE AUTHORITY RANKING
        # =========================================

        valid_results.sort(
            key=lambda result: self.SOURCE_PRIORITY.get(
                str(
                    result.get(
                        "source_type",
                        ""
                    )
                ).lower(),
                0
            ),
            reverse=True
        )

        query_lower = query.lower()

        # =========================================
        # ESCALATION / PRIORITY / SLA QUERIES
        # =========================================

        escalation_keywords = [
            "priority",
            "escalation",
            "p1",
            "severity",
            "sla"
        ]

        if any(
            word in query_lower
            for word in escalation_keywords
        ):

            preferred_types = {
                "customer_agreement",
                "current_sop",
                "current_policy"
            }

            filtered_results = [
                result
                for result in valid_results
                if str(
                    result.get(
                        "source_type",
                        ""
                    )
                ).lower()
                in preferred_types
            ]

            if filtered_results:
                return filtered_results[:top_k]

        # =========================================
        # CANCELLATION / SERVICE CREDIT QUERIES
        # =========================================

        decision_keywords = [
            "cancel",
            "cancellation",
            "refund",
            "credit",
            "service credit",
            "fee"
        ]

        if any(
            word in query_lower
            for word in decision_keywords
        ):

            preferred_types = {
                "customer_agreement",
                "current_sop",
                "current_policy"
            }

            filtered_results = [
                result
                for result in valid_results
                if str(
                    result.get(
                        "source_type",
                        ""
                    )
                ).lower()
                in preferred_types
            ]

            if filtered_results:
                return filtered_results[:top_k]

        return valid_results[:top_k]

    def format_context(
        self,
        results
    ):
        """
        Convert retrieved chunks into a readable
        context string for the AI agent.
        """

        if not results:
            return "No relevant documents found."

        context_parts = []

        for index, result in enumerate(
            results,
            start=1
        ):

            source = result.get(
                "source",
                "Unknown"
            )

            page = result.get(
                "page",
                "Unknown"
            )

            source_type = result.get(
                "source_type",
                "general_document"
            )

            text = result.get(
                "text",
                ""
            )

            context_parts.append(
                f"""
[SOURCE {index}]
Document: {source}
Page: {page}
Source Type: {source_type}

{text}
"""
            )

        return "\n".join(
            context_parts
        )

    def get_citations(
        self,
        results
    ):
        """
        Extract unique source citations and keep them
        ordered by source authority.
        """

        citations = []
        seen = set()

        for result in results:

            citation = {
                "source": result.get(
                    "source",
                    "Unknown"
                ),
                "page": result.get(
                    "page",
                    "Unknown"
                ),
                "source_type": result.get(
                    "source_type",
                    "general_document"
                )
            }

            key = (
                citation["source"],
                citation["page"]
            )

            if key not in seen:

                citations.append(
                    citation
                )

                seen.add(key)

        citations.sort(
            key=lambda citation: self.SOURCE_PRIORITY.get(
                str(
                    citation["source_type"]
                ).lower(),
                0
            ),
            reverse=True
        )

        return citations