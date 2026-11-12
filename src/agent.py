from functools import lru_cache
import re
import uuid

from src.workflow import detect_workflow

from src.tools.cancellation_tools import (
    check_cancellation,
    cancel_order
)
from src.tools.ticket_tools import lookup_ticket
from src.tools.service_credit_tools import check_service_credit
from src.tools.order_tools import (
    lookup_order,
    lookup_account
)

from src.escalation_action import create_escalation
from src.response_generator import (
    generate_response,
    generate_fallback_response
)
from src.guardrails import validate_input, validate_output
from src.tracing import traced


def normalize_answer(answer):
    """Convert escaped newline sequences into actual line breaks."""
    if isinstance(answer, str):
        return (
            answer
            .replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\r", "\n")
        )
    return answer


@traced(name="parcelpilot.retriever_initialization")
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
        self.pending_cancellation = None

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
        selected_account = (
            str(account_id).strip().upper()
            if account_id else None
        )

        # =========================================
        # HANDLE CANCELLATION CONFIRMATION
        # =========================================

        if getattr(self, "pending_cancellation", None):
            pending = self.pending_cancellation

            # YES -> REVALIDATE AND EXECUTE CANCELLATION
            if query_lower in {
                "yes",
                "y",
                "confirm",
                "confirmed",
                "proceed",
                "confirm cancellation"
            }:
                # Clear pending state before performing the action.
                self.pending_cancellation = None

                # Ensure the active account has not changed.
                if selected_account != pending["account_id"]:
                    return {
                        "query": query,
                        "answer": (
                            "# Cancellation Rejected\n\n"
                            "The selected account has changed. "
                            "No cancellation was performed."
                        ),
                        "structured_data": {
                            "workflow": "cancellation"
                        },
                        "citations": [],
                        "status": "blocked_access"
                    }

                # Revalidate eligibility and account ownership.
                eligibility = check_cancellation(
                    pending["order_id"],
                    selected_account
                )

                if not eligibility.get("can_cancel"):
                    return {
                        "query": query,
                        "answer": (
                            "# Cancellation Not Completed\n\n"
                            + eligibility.get(
                                "reason",
                                eligibility.get(
                                    "message",
                                    "The order is no longer eligible for cancellation."
                                )
                            )
                        ),
                        "structured_data": {
                            "workflow": "cancellation",
                            "cancellation": eligibility
                        },
                        "citations": [],
                        "status": "validation_failed"
                    }

                # Execute the SQLite cancellation.
                result = cancel_order(
                    order_id=pending["order_id"],
                    account_id=selected_account
                )

                if result.get("success"):
                    return {
                        "query": query,
                        "answer": (
                            "# Cancellation Successful\n\n"
                            "Your shipment has been cancelled successfully.\n\n"
                            f"- **Order ID:** {result['order_id']}\n"
                            f"- **Account ID:** {result['account_id']}\n"
                            f"- **Status:** {result['status']}\n"
                            f"- **Cancelled At:** {result['cancelled_at']}"
                        ),
                        "structured_data": {
                            "workflow": "cancellation",
                            "cancellation": result
                        },
                        "citations": [],
                        "status": "cancellation_success"
                    }

                return {
                    "query": query,
                    "answer": (
                        "# Cancellation Failed\n\n"
                        + result.get(
                            "message",
                            "The cancellation could not be completed."
                        )
                    ),
                    "structured_data": {
                        "workflow": "cancellation",
                        "cancellation": result
                    },
                    "citations": [],
                    "status": "cancellation_failed"
                }

            # NO -> KEEP SHIPMENT ACTIVE
            if query_lower in {
                "no",
                "n",
                "don't cancel",
                "do not cancel",
                "keep it active",
                "keep the shipment active"
            }:
                self.pending_cancellation = None

                return {
                    "query": query,
                    "answer": (
                        "# Cancellation Declined\n\n"
                        f"Order {pending['order_id']} remains unchanged. "
                        "No cancellation was performed."
                    ),
                    "structured_data": {
                        "workflow": "cancellation"
                    },
                    "citations": [],
                    "status": "cancellation_declined"
                }

            # INVALID CONFIRMATION
            return {
                "query": query,
                "answer": (
                    "# Cancellation Confirmation Required\n\n"
                    f"Order {pending['order_id']} is awaiting confirmation.\n\n"
                    "Reply **Yes** to cancel or **No** to keep the shipment active."
                ),
                "structured_data": {
                    "workflow": "cancellation"
                },
                "citations": [],
                "status": "pending_confirmation"
            }

        # =========================================
        # HANDLE ESCALATION CONFIRMATION
        # =========================================

        if self.pending_escalation:
            pending = self.pending_escalation

            # YES -> CREATE ESCALATION
            if query_lower in {
                "yes",
                "y",
                "confirm",
                "confirmed"
            }:
                # Ensure the selected account has not changed.
                pending_account = pending.get("account_id")
                if selected_account is not None and selected_account != pending_account:
                    self.pending_escalation = None
                    return {
                        "query": query,
                        "answer": (
                            "# Escalation Not Created\n\n"
                            "The selected account has changed. "
                            "No escalation was created."
                        ),
                        "structured_data": {
                            "workflow": "escalation"
                        },
                        "citations": [],
                        "status": "blocked_access"
                    }

                # Revalidate ticket ownership immediately before the side effect.
                ticket_check = lookup_ticket(
                    ticket_id=pending["ticket_id"],
                    account_id=pending_account
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
                        "structured_data": {
                            "workflow": "escalation"
                        },
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
            if query_lower in {
                "no",
                "n",
                "cancel",
                "cancel escalation"
            }:
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
                    "Reply **Yes** to create the escalation "
                    "or **No** to cancel it."
                ),
                "structured_data": {
                    "workflow": "escalation"
                },
                "citations": [],
                "status": "pending_confirmation"
            }

        # =========================================
        # HANDLE ORPHANED CONFIRMATION
        # =========================================

        if query_lower in {
            "yes",
            "y",
            "confirm",
            "confirmed",
            "proceed",
            "no",
            "n",
            "cancel",
            "cancel escalation",
            "don't cancel",
            "do not cancel",
            "keep it active"
        }:
            return {
                "query": query,
                "answer": (
                    "There is no pending escalation or cancellation awaiting confirmation. "
                    "Please submit a new cancellation or escalation request."
                ),
                "structured_data": {},
                "citations": [],
                "status": "no_pending_confirmation"
            }

        # =========================================
        # CROSS-ACCOUNT ACCESS CONTROL
        # =========================================
        # The account selected in the sidebar is the scope for this request.
        # Never let an explicit request for another account fall through to
        # generic order/shipment intent detection or RAG.

        requested_accounts = {
            value.upper()
            for value in re.findall(
                r"\bACCT-\d+\b",
                query,
                flags=re.IGNORECASE
            )
        }

        other_accounts = sorted(
            value for value in requested_accounts
            if value != selected_account
        )

        bulk_customer_request = bool(re.search(
            r"\b(all|every)\s+(customer|customers|customer accounts|accounts)\b"
            r"|\b(all customers'?(?: private)? (?:data|records|agreements|shipments))\b",
            query,
            flags=re.IGNORECASE
        ))

        if other_accounts or bulk_customer_request:
            scope_message = (
                f" The active account scope is **{selected_account}**."
                if selected_account else
                " Select a valid customer account before requesting account-specific information."
            )

            answer = (
                "## Access Restricted\n\n"
                "I can only retrieve customer agreements, orders, and shipment "
                "records within the currently selected account. I cannot access "
                "private records belonging to another customer or enumerate all customers."
                + scope_message
                + "\n\nNo cross-account data was retrieved or disclosed."
            )

            return {
                "query": query,
                "answer": answer,
                "structured_data": {
                    "workflow": "access_control",
                    "status": "blocked",
                    "selected_account": selected_account,
                    "requested_other_accounts": len(other_accounts)
                },
                "citations": [],
                "status": "blocked_access"
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
            context_data["account"] = lookup_account(account_id)

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
                    "can_cancel": False,
                    "message": (
                        "Please provide a valid Order ID "
                        "to check cancellation eligibility."
                    )
                }

            else:
                order_result = context_data.get("order", {})

                if order_result.get("found"):
                    eligibility = check_cancellation(
                        order_id,
                        account_id
                    )
                    context_data["cancellation"] = eligibility

                    if eligibility.get("can_cancel"):
                        if self.pending_escalation:
                            return {
                                "query": query,
                                "answer": (
                                    "Please complete or decline the pending "
                                    "escalation before requesting cancellation."
                                ),
                                "structured_data": context_data,
                                "citations": [],
                                "status": "pending_confirmation"
                            }

                        self.pending_cancellation = {
                            "order_id": str(order_id).strip().upper(),
                            "account_id": selected_account
                        }

                        return {
                            "query": query,
                            "answer": (
                                "# Cancellation Confirmation Required\n\n"
                                f"Order **{order_id}** is eligible for cancellation.\n\n"
                                "Do you want to proceed with cancellation?\n\n"
                                "**Yes** - Confirm cancellation\n\n"
                                "**No** - Keep shipment active"
                            ),
                            "structured_data": context_data,
                            "citations": [],
                            "status": "pending_confirmation"
                        }

                else:
                    context_data["cancellation"] = {
                        "allowed": False,
                        "can_cancel": False,
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
                order_result = context_data.get("order", {})

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
            # Do not overwrite a pending cancellation confirmation.
            if self.pending_cancellation:
                return {
                    "query": query,
                    "answer": (
                        "Please complete or decline the pending "
                        "cancellation before requesting an escalation."
                    ),
                    "structured_data": context_data,
                    "citations": [],
                    "status": "pending_confirmation"
                }

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

            ticket_data = context_data.get("ticket", {})

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
                "account_id": selected_account,
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

        if workflow in {
            "order",
            "cancellation",
            "service_credit",
            "account"
        }:
            answer = normalize_answer(
                generate_fallback_response(query, context_data)
            )
            output_ok, safe_answer = validate_output(answer)

            return {
                "query": query,
                "answer": safe_answer if not output_ok else answer,
                "structured_data": context_data,
                "citations": [],
                "status": (
                    "fallback_response"
                    if output_ok
                    else "blocked_output"
                )
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

            response = generate_response(
                query=query,
                structured_data=context_data,
                context=context,
                citations=citations
            )

            if isinstance(response, dict) and "answer" in response:
                response["answer"] = normalize_answer(response["answer"])

            return response

        except Exception as error:
            # Keep the chat available if retrieval or model loading fails.
            print(f"ParcelPilot retrieval fallback: {error}")

            answer = normalize_answer(
                generate_fallback_response(query, context_data)
            )

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
                "status": (
                    "fallback_response"
                    if output_ok
                    else "blocked_output"
                )
            }
