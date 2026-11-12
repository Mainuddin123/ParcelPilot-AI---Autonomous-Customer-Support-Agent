
import re


def detect_workflow(query: str):
    q = query.lower().strip()

    # =========================================
    # CANCELLATION WORKFLOW
    # =========================================

    cancellation_patterns = [
        r"\bcan i cancel\b",
        r"\bcancel(?:\s+my)?\s+order\b",
        r"\bcancel(?:\s+my)?\s+shipment\b",
        r"\bcancel(?:\s+my)?\s+parcel\b",
        r"\bi want to cancel\b",
        r"\bi need to cancel\b",
        r"\bplease cancel\b",
        r"\bcancel\s+ord-\d+\b",
        r"\bcancel\s+the\s+shipment\b",
        r"\bstop\s+(?:my\s+)?shipment\b",
        r"\bstop\s+(?:my\s+)?parcel\b",
        r"\brequest cancellation\b",
        r"\binitiate cancellation\b",
        r"\bwithdraw.*shipment\b",
    ]

    if any(re.search(pattern, q) for pattern in cancellation_patterns):
        return "cancellation"

    # =========================================
    # SERVICE CREDIT WORKFLOW
    # =========================================

    service_credit = [
        "service credit",
        "credit eligibility",
        "eligible for credit",
        "eligible for compensation",
        "claim compensation",
        "request compensation",
        "claim refund",
        "request a refund",
        "delivery compensation"
    ]

    if any(term in q for term in service_credit):
        return "service_credit"

    # =========================================
    # ESCALATION WORKFLOW
    # =========================================

    escalation_actions = [
        "escalate ticket",
        "escalate my ticket",
        "escalate my issue",
        "escalate this issue",
        "escalate this ticket",
        "i want to escalate",
        "please escalate",
        "raise an escalation",
        "raise escalation",
        "create an escalation",
        "create escalation",
        "submit an escalation",
        "submit escalation",
        "mark as urgent",
        "mark this as priority"
    ]

    if any(term in q for term in escalation_actions):
        return "escalation"

    # =========================================
    # POLICY INFORMATION -> RAG
    # =========================================

    policy_terms = [
        "policy",
        "policies",
        "sla",
        "sop",
        "terms and conditions",
        "escalation process",
        "cancellation rules",
        "cancellation policy",
        "refund rules",
        "refund policy",
        "service credit rules"
    ]

    if any(term in q for term in policy_terms):
        return "general"

    # =========================================
    # TICKET WORKFLOW
    # =========================================

    ticket_terms = [
        "ticket status",
        "check ticket",
        "ticket details",
        "support request status",
        "support case",
        "case status",
        "issue status"
    ]

    if any(term in q for term in ticket_terms):
        return "ticket"

    # =========================================
    # ORDER WORKFLOW
    # =========================================

    order_terms = [
        "order",
        "parcel",
        "shipment",
        "delivery",
        "tracking",
        "pickup"
    ]

    if any(term in q for term in order_terms):
        return "order"

    # =========================================
    # ACCOUNT WORKFLOW
    # =========================================

    account_terms = [
        "account",
        "my plan",
        "support available",
        "premium support",
        "account status"
    ]

    if any(term in q for term in account_terms):
        return "account"

    return "general"
