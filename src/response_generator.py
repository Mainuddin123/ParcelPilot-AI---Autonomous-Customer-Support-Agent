
import time
from functools import lru_cache

from src.llm import GeminiLLM
from src.guardrails import validate_output
from src.tracing import traced


def generate_fallback_response(query, structured_data):

    workflow = structured_data.get("workflow", "")
    order_data = structured_data.get("order", {})
    account_data = structured_data.get("account", {})
    cancellation_data = structured_data.get("cancellation", {})
    service_credit_data = structured_data.get("service_credit", {})

    # =========================================
    # MISSING ORDER DATA
    # =========================================

    if workflow in {"order", "cancellation", "service_credit"} and not order_data:

        if workflow == "cancellation":
            return (
                "# Cancellation Verification\n\n"
                "Please provide a valid Order ID so I can "
                "verify cancellation eligibility."
            )

        if workflow == "service_credit":
            return (
                "# Service Credit Verification\n\n"
                "Please provide a valid Order ID so I can "
                "verify service-credit eligibility."
            )

        return (
            "# Order Information\n\n"
            "Please provide a valid Order ID so I can look up the order."
        )

    # =========================================
    # ORDER NOT FOUND
    # =========================================

    if order_data and not order_data.get("found"):

        message = order_data.get(
            "reason",
            "The order could not be found."
        )

        if workflow == "service_credit":
            return (
                "# Service Credit Verification\n\n"
                "We could not verify service-credit eligibility.\n\n"
                f"{message}"
            )

        if workflow == "cancellation":
            return (
                "# Cancellation Verification\n\n"
                "We could not verify cancellation eligibility.\n\n"
                f"{message}"
            )

        return f"# Order Information\n\n{message}"

    # =========================================
    # CANCELLATION RESPONSE
    # =========================================

    if workflow == "cancellation":

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
            return (
                "# Cancellation Decision\n\n"
                "Your order is eligible for cancellation.\n\n"
                f"{message}"
            )

        return (
            "# Cancellation Decision\n\n"
            "Your order is not eligible for cancellation.\n\n"
            f"{message}"
        )

    # =========================================
    # SERVICE CREDIT RESPONSE
    # =========================================

    if workflow == "service_credit":

        eligible = service_credit_data.get("eligible", False)

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
            return (
                "# Service Credit Decision\n\n"
                "You are eligible for a service credit.\n\n"
                f"- **Credit Amount:** ₹{credit_amount}\n\n"
                f"**Reason:** {reason}"
            )

        return (
            "# Service Credit Decision\n\n"
            "You are not eligible for a service credit.\n\n"
            f"**Reason:** {reason}"
        )

    # =========================================
    # ORDER RESPONSE
    # =========================================

    if order_data.get("found"):

        order = order_data.get("order", {})
        issues = order_data.get("issues", [])

        order_id = order.get("order_id", "Unknown")
        status = order.get("status", "Unknown")
        carrier = order.get("carrier", "Unknown")

        pickup_start = order.get("pickup_window_start")
        pickup_end = order.get("pickup_window_end")
        pickup_actual = order.get("pickup_actual_at")

        def clean_value(value):
            if value is None or str(value).lower() in {"nan", "none", ""}:
                return "Not available"
            return value

        pickup_start = clean_value(pickup_start)
        pickup_end = clean_value(pickup_end)
        pickup_actual = clean_value(pickup_actual)

        answer = f"""# Order Information

Based on the available order information:

- **Order ID:** {order_id}
- **Carrier:** {carrier}
- **Current Status:** {status}
- **Scheduled Pickup Window:** {pickup_start} to {pickup_end}
- **Actual Pickup Time:** {pickup_actual}
"""

        if issues:
            answer += "\n### Important Notice\n\n"

            for issue in issues:
                answer += f"- ⚠️ {issue}\n"

        answer += (
            "\nThis response is based on the "
            "available structured order data."
        )

        return answer

    # =========================================
    # ACCOUNT RESPONSE
    # =========================================

    if workflow == "account" and account_data.get("found"):

        account = account_data.get("account", {})

        return f"""# Account Information

Based on the available account information:

- **Account:** {account.get("account_name", "Unknown")}
- **Plan:** {account.get("plan", "Unknown")}
- **Status:** {account.get("status", "Unknown")}

This response is based on the available structured account data."""

    return (
        "The requested information could not be found "
        "in the available structured data."
    )


# =============================================
# SHARED GEMINI CLIENT
# =============================================

@lru_cache(maxsize=1)
def _get_shared_llm():
    return GeminiLLM()


# =============================================
# RESPONSE GENERATION
# =============================================

@traced(name="parcelpilot.response_generation")
def generate_response(
    query,
    structured_data,
    context,
    citations
):

    total_start = time.perf_counter()

    # 1. Reuse Gemini client.
    llm = _get_shared_llm()

    # 2. Construct prompt.
    prompt_start = time.perf_counter()

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

9. If information is insufficient or conflicting,
clearly state the uncertainty instead of guessing.

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

    prompt_time = (
        time.perf_counter() - prompt_start
    ) * 1000

    print(f"[PERF] Prompt construction: {prompt_time:.2f} ms")

    # 3. Gemini generation.
    generation_start = time.perf_counter()

    try:

        answer = llm.generate(prompt)

        status = "success"

    except Exception as error:

        print(f"[LLM] Generation failed: {error}")

        answer = generate_fallback_response(
            query,
            structured_data
        )

        status = "fallback_response"

    generation_time = (
        time.perf_counter() - generation_start
    ) * 1000

    print(f"[PERF] Gemini generation: {generation_time:.2f} ms")

    # 4. Output validation.
    validation_start = time.perf_counter()

    output_ok, safe_answer = validate_output(answer)

    validation_time = (
        time.perf_counter() - validation_start
    ) * 1000

    print(f"[PERF] Output validation: {validation_time:.2f} ms")

    if not output_ok:
        answer = safe_answer
        status = "blocked_output"

    # 5. Total response generation time.
    total_time = (
        time.perf_counter() - total_start
    ) * 1000

    print(f"[PERF] Total response generation: {total_time:.2f} ms")

    return {
        "query": query,
        "answer": answer,
        "structured_data": structured_data,
        "citations": citations,
        "status": status
    }
