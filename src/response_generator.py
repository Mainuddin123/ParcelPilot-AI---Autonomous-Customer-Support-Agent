from functools import lru_cache

from src.llm import GeminiLLM
from src.guardrails import validate_output
from src.tracing import traced


def generate_fallback_response(
    query,
    structured_data
):
    workflow = structured_data.get(
        "workflow",
        ""
    )

    order_data = structured_data.get(
        "order",
        {}
    )

    account_data = structured_data.get(
        "account",
        {}
    )

    cancellation_data = structured_data.get(
        "cancellation",
        {}
    )

    # Do not infer a decision when an order identifier/data is missing.
    if workflow in {"order", "cancellation", "service_credit"} and not order_data:
        if workflow == "cancellation":
            return "# Cancellation Verification\\n\\nPlease provide a valid Order ID so I can verify cancellation eligibility."
        if workflow == "service_credit":
            return "# Service Credit Verification\\n\\nPlease provide a valid Order ID so I can verify service-credit eligibility."
        return "# Order Information\\n\\nPlease provide a valid Order ID so I can look up the order."

    service_credit_data = structured_data.get(
        "service_credit",
        {}
    )

    # =========================================
    # ORDER ACCESS / NOT FOUND
    # =========================================

    if order_data and not order_data.get("found"):

        message = order_data.get(
            "reason",
            "The order could not be found."
        )

        if workflow == "service_credit":

            return f"""# Service Credit Verification

We could not verify service-credit eligibility because the order was not found or could not be accessed.

{message}"""

        if workflow == "cancellation":

            return f"""# Cancellation Verification

We could not verify cancellation eligibility because the order was not found or could not be accessed.

{message}"""

        return f"""# Order Information

{message}"""

    # =========================================
    # CANCELLATION RESPONSE
    # =========================================

    if workflow == "cancellation":

        # The cancellation tool historically returned "can_cancel".
        # Accept that field while standardizing on "allowed".
        allowed = cancellation_data.get(
            "allowed",
            cancellation_data.get("can_cancel", False)
        )

        message = cancellation_data.get(
            "message",
            cancellation_data.get(
                "reason",
                "Cancellation information is unavailable."
            )
        )

        if allowed:

            return f"""# Cancellation Decision

Your order is eligible for cancellation.

{message}"""

        return f"""# Cancellation Decision

Your order is not eligible for cancellation.

{message}"""

    # =========================================
    # SERVICE CREDIT RESPONSE
    # =========================================

    if workflow == "service_credit":

        eligible = service_credit_data.get(
            "eligible",
            False
        )

        reason = service_credit_data.get(
            "reason",
            service_credit_data.get(
                "message",
                "Service credit information is unavailable."
            )
        )

        credit_amount = service_credit_data.get(
            "credit_amount_inr",
            0
        )

        if eligible:

            return f"""# Service Credit Decision

You are eligible for a service credit.

- **Credit Amount:** ₹{credit_amount}

**Reason:** {reason}"""

        return f"""# Service Credit Decision

You are not eligible for a service credit.

**Reason:** {reason}"""

    # =========================================
    # ORDER RESPONSE
    # =========================================

    if order_data.get("found"):

        order = order_data.get(
            "order",
            {}
        )

        issues = order_data.get(
            "issues",
            []
        )

        order_id = order.get(
            "order_id",
            "Unknown"
        )

        status = order.get(
            "status",
            "Unknown"
        )

        carrier = order.get(
            "carrier",
            "Unknown"
        )

        pickup_start = order.get(
            "pickup_window_start"
        )

        pickup_end = order.get(
            "pickup_window_end"
        )

        pickup_actual = order.get(
            "pickup_actual_at"
        )

        # Handle missing / NaN values

        if (
            pickup_start is None
            or str(pickup_start).lower() == "nan"
        ):
            pickup_start = "Not available"

        if (
            pickup_end is None
            or str(pickup_end).lower() == "nan"
        ):
            pickup_end = "Not available"

        if (
            pickup_actual is None
            or str(pickup_actual).lower() == "nan"
        ):
            pickup_actual = "Not available"

        answer = f"""# Order Information

Based on the available order information:

- **Order ID:** {order_id}
- **Carrier:** {carrier}
- **Current Status:** {status}
- **Scheduled Pickup Window:** {pickup_start} to {pickup_end}
- **Actual Pickup Time:** {pickup_actual}
"""

        # =====================================
        # PROACTIVE ISSUE INFORMATION
        # =====================================

        if issues:

            answer += "\n### Important Notice\n\n"

            for issue in issues:

                answer += (
                    f"- ⚠️ {issue}\n"
                )

        answer += (
            "\nThis response is based on the "
            "available structured order data."
        )

        return answer

    # =========================================
    # ACCOUNT RESPONSE
    # =========================================

    if account_data.get("found"):

        account = account_data.get(
            "account",
            {}
        )

        return f"""# Account Information

Based on the available account information:

- **Account:** {account.get("account_name", "Unknown")}
- **Plan:** {account.get("plan", "Unknown")}
- **Status:** {account.get("status", "Unknown")}

This response is based on the available structured account data."""

    # =========================================
    # DEFAULT RESPONSE
    # =========================================

    return (
        "The requested information could not be found "
        "in the available structured data."
    )


@lru_cache(maxsize=1)
def _get_shared_llm():
    """Reuse the Gemini client instead of recreating it for every request."""
    return GeminiLLM()


@traced(name="parcelpilot.response_generation")
def generate_response(
    query,
    structured_data,
    context,
    citations
):
    llm = _get_shared_llm()

    prompt = f"""
You are ParcelPilot AI, a customer support decision assistant.

Answer the user's question using ONLY the provided
structured data and retrieved documents.

RULES:

1. Do not invent information.

2. Structured data is the source of truth for:
   - Order information
   - Account information
   - Ticket information
   - Cancellation decisions
   - Service credit decisions

3. Source authority for policy decisions is:

   Customer-specific agreement
   > Current SOP
   > Current policy
   > General documents

4. Never use deprecated, obsolete, or archived
documents as a source of truth.

5. If structured order data contains detected issues,
proactively inform the user about those issues.

6. Clearly explain decisions.

7. If cancellation is not allowed,
explain why.

8. If service credit is not allowed,
explain why.

9. If the available information is insufficient
or conflicting, clearly state the uncertainty
instead of guessing.

10. Mention only the sources actually provided
in the retrieved context.

11. Be concise, clear, and professional.

USER QUESTION:
{query}

STRUCTURED DATA:
{structured_data}

RETRIEVED DOCUMENT CONTEXT:
{context}

CITATIONS:
{citations}

Provide the final customer support answer.
"""

    try:

        answer = llm.generate(
            prompt
        )

        status = "success"

    except Exception as error:

        print(
            f"\nLLM generation failed: {error}\n"
        )

        answer = generate_fallback_response(
            query,
            structured_data
        )

        status = "fallback_response"

    output_ok, safe_answer = validate_output(answer)
    if not output_ok:
        answer = safe_answer
        status = "blocked_output"

    return {
        "query": query,
        "answer": answer,
        "structured_data": structured_data,
        "citations": citations,
        "status": status
    }