from functools import lru_cache
import uuid

from src.workflow import detect_workflow

from src.tools.cancellation_tools import check_cancellation
from src.tools.ticket_tools import lookup_ticket
from src.tools.service_credit_tools import check_service_credit

from src.tools.order_tools import (
    lookup_order,
    lookup_account
)

from src.escalation_action import create_escalation
from src.response_generator import generate_response, generate_fallback_response
from src.guardrails import validate_input, validate_output
from src.tracing import traced


@lru_cache(maxsize=1)
def _get_shared_retriever():
    """Import and load the read-only RAG stack only for the first RAG query."""
    from src.rag.retriever import Retriever
    return Retriever()


class ParcelPilotAgent:

    def __init__(self):
        # Load embedding/vector/reranking models only when a RAG query needs them.
        self.retriever = None
        self.pending_escalation = None

    @traced(name="parcelpilot.agent_process")
    def process(
        self,
        query: str,
        account_id: str = None,
        order_id: str = None,
        ticket_id: str = None
    ):

        is_valid, rejection = validate_input(query)
        if not is_valid:
            return {
                "query": query,
                "answer": rejection,
                "structured_data": {"workflow": "guardrail"},
                "citations": [],
                "status": "blocked_input"
            }

        query_lower = query.lower().strip()

        # =========================================
        # HANDLE ESCALATION CONFIRMATION
        # =========================================

        if self.pending_escalation:

            # YES -> CREATE ESCALATION
            if query_lower in [
                "yes",
                "y",
                "confirm",
                "confirmed"
            ]:

                pending = self.pending_escalation

                # Revalidate ticket ownership immediately before the side effect.
                ticket_check = lookup_ticket(
                    ticket_id=pending["ticket_id"],
                    account_id=pending.get("account_id")
                )
                if not ticket_check.get("found"):
                    self.pending_escalation = None
                    return {
                        "query": query,
                        "answer": (
                            "# Escalation Not Created\n\n"
                            "The ticket could not be revalidated for this account. "
                            "No escalation was created."
                        ),
                        "structured_data": {"workflow": "escalation"},
                        "citations": [],
                        "status": "validation_failed"
                    }

                result = create_escalation(
                    ticket_id=pending["ticket_id"],
                    reason=pending["reason"],
                    idempotency_key=pending["idempotency_key"]
                )

                self.pending_escalation = None

                heading = (
                    "# Escalation Already Exists"
                    if result.get("already_exists")
                    else "# Escalation Created"
                )
                intro = (
                    "An escalation is already recorded for this ticket."
                    if result.get("already_exists")
                    else "The escalation has been created successfully."
                )
                return {
                    "query": query,
                    "answer": (
                        f"{heading}\n\n{intro}\n\n"
                        f"- **Escalation ID:** {result['escalation_id']}\n"
                        f"- **Ticket ID:** {result['ticket_id']}\n"
                        f"- **Status:** {result['status']}"
                    ),
                    "structured_data": {
                        "workflow": "escalation",
                        "escalation": result
                    },
                    "citations": [],
                    "status": "success"
                }

            # NO -> CANCEL ESCALATION
            if query_lower in [
                "no",
                "n",
                "cancel",
                "cancel escalation"
            ]:

                self.pending_escalation = None

                return {
                    "query": query,
                    "answer": (
                        "# Escalation Cancelled\n\n"
                        "The escalation action was cancelled. "
                        "No escalation was created."
                    ),
                    "structured_data": {
                        "workflow": "escalation"
                    },
                    "citations": [],
                    "status": "success"
                }

            # INVALID CONFIRMATION
            return {
                "query": query,
                "answer": (
                    "# Escalation Confirmation Required\n\n"
                    "An escalation is waiting for your confirmation.\n\n"
                    "Please reply **Yes** to create the escalation "
                    "or **No** to cancel it."
                ),
                "structured_data": {
                    "workflow": "escalation"
                },
                "citations": [],
                "status": "pending_confirmation"
            }

        # Do not interpret an orphaned Yes/No as a new RAG question or action.
        if query_lower in {"yes", "y", "confirm", "confirmed", "no", "n", "cancel", "cancel escalation"}:
            return {
                "query": query,
                "answer": (
                    "There is no pending escalation confirmation. "
                    "Please submit a new escalation request if you need one."
                ),
                "structured_data": {"workflow": "escalation"},
                "citations": [],
                "status": "no_pending_confirmation"
            }

        # =========================================
        # NORMAL WORKFLOW DETECTION
        # =========================================

        context_data = {}

        workflow = detect_workflow(query)

        context_data["workflow"] = workflow

        # =========================================
        # ACCOUNT LOOKUP
        # =========================================

        if account_id:

            context_data["account"] = lookup_account(
                account_id
            )

        # =========================================
        # ORDER LOOKUP WITH ACCESS CONTROL
        # =========================================

        if order_id:

            context_data["order"] = lookup_order(
                order_id=order_id,
                account_id=account_id
            )

        # =========================================
        # TICKET LOOKUP WITH ACCESS CONTROL
        # =========================================

        if ticket_id:

            context_data["ticket"] = lookup_ticket(
                ticket_id=ticket_id,
                account_id=account_id
            )

        # =========================================
        # CANCELLATION WORKFLOW
        # =========================================

        if workflow == "cancellation":

            if not order_id:

                context_data["cancellation"] = {
                    "allowed": False,
                    "message": (
                        "Please provide a valid Order ID "
                        "to check cancellation eligibility."
                    )
                }

            else:

                order_result = context_data.get(
                    "order",
                    {}
                )

                if order_result.get("found"):

                    context_data["cancellation"] = (
                        check_cancellation(order_id)
                    )

                else:

                    context_data["cancellation"] = {
                        "allowed": False,
                        "message": (
                            "Cancellation cannot be checked because "
                            "the order was not found or does not belong "
                            "to the provided account."
                        )
                    }

        # =========================================
        # SERVICE CREDIT WORKFLOW
        # =========================================

        if workflow == "service_credit":

            if not order_id:

                context_data["service_credit"] = {
                    "eligible": False,
                    "message": (
                        "Please provide a valid Order ID "
                        "to check service credit eligibility."
                    )
                }

            else:

                order_result = context_data.get(
                    "order",
                    {}
                )

                if order_result.get("found"):

                    context_data["service_credit"] = (
                        check_service_credit(order_id)
                    )

                else:

                    context_data["service_credit"] = {
                        "eligible": False,
                        "message": (
                            "Service credit cannot be checked because "
                            "the order was not found or does not belong "
                            "to the provided account."
                        )
                    }

        # =========================================
        # ESCALATION WORKFLOW
        # =========================================

        if workflow == "escalation":

            # NO TICKET ID
            if not ticket_id:

                return {
                    "query": query,
                    "answer": (
                        "# Escalation Request\n\n"
                        "Please provide a valid Ticket ID before "
                        "an escalation can be created."
                    ),
                    "structured_data": context_data,
                    "citations": [],
                    "status": "missing_ticket_id"
                }

            ticket_data = context_data.get(
                "ticket",
                {}
            )

            # INVALID TICKET
            if not ticket_data.get("found"):

                return {
                    "query": query,
                    "answer": (
                        "# Escalation Request\n\n"
                        "The specified ticket could not be found "
                        "or does not belong to the provided account."
                    ),
                    "structured_data": context_data,
                    "citations": [],
                    "status": "ticket_not_found"
                }

            # VALID TICKET -> STORE PENDING ESCALATION
            self.pending_escalation = {
                "ticket_id": ticket_id.strip().upper(),
                "account_id": account_id.strip().upper() if account_id else None,
                "reason": query,
                "idempotency_key": str(uuid.uuid4())
            }

            return {
                "query": query,
                "answer": (
                    "# Escalation Confirmation Required\n\n"
                    f"I found ticket **{ticket_id}**.\n\n"
                    "Do you confirm that you want to create "
                    "an escalation for this ticket?\n\n"
                    "Reply **Yes** to confirm or **No** to cancel."
                ),
                "structured_data": context_data,
                "citations": [],
                "status": "pending_confirmation"
            }

        # =========================================
        # STRUCTURED WORKFLOW FAST PATH
        # =========================================
        # Order and policy decisions already come from validated structured
        # records/tools. Do not initialize retrieval models or call Gemini.
        if workflow in {"order", "cancellation", "service_credit", "account"}:
            answer = generate_fallback_response(query, context_data)
            output_ok, safe_answer = validate_output(answer)
            return {
                "query": query,
                "answer": safe_answer if not output_ok else answer,
                "structured_data": context_data,
                "citations": [],
                "status": "fallback_response" if output_ok else "blocked_output"
            }

        # =========================================
        # DOCUMENT RETRIEVAL (LAZY INITIALIZATION)
        # =========================================
        try:
            retriever = getattr(self, "retriever", None)
            if retriever is None:
                retriever = _get_shared_retriever()
                self.retriever = retriever

            results = retriever.retrieve(
                query=query,
                account_id=account_id
            )
            context = retriever.format_context(results)
            citations = retriever.get_citations(results)

            return generate_response(
                query=query,
                structured_data=context_data,
                context=context,
                citations=citations
            )

        except Exception as error:
            # Keep the chat available if retrieval or model loading fails.
            print(f"ParcelPilot retrieval fallback: {error}")
            answer = generate_fallback_response(query, context_data)
            answer += (
                "\n\n**Note:** Policy-document retrieval is temporarily "
                "unavailable. This response uses only available structured "
                "records; retry later for document-based policy details."
            )
            output_ok, safe_answer = validate_output(answer)
            return {
                "query": query,
                "answer": safe_answer if not output_ok else answer,
                "structured_data": context_data,
                "citations": [],
                "status": "fallback_response" if output_ok else "blocked_output"
            }
