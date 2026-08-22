def detect_workflow(query: str):
    """
    Detect the appropriate customer support workflow
    based on the user's query.
    """

    query_lower = query.lower().strip()

    # Cancellation workflow
    cancellation_keywords = [
        "cancel",
        "cancellation",
        "cancel my order",
        "stop shipment",
        "stop my parcel"
    ]

    if any(keyword in query_lower for keyword in cancellation_keywords):
        return "cancellation"

    # Service credit workflow
    service_credit_keywords = [
        "service credit",
        "credit",
        "compensation",
        "refund",
        "claim refund",
        "delivery compensation"
    ]

    if any(keyword in query_lower for keyword in service_credit_keywords):
        return "service_credit"

    # Escalation workflow
    escalation_keywords = [
        "priority",
        "escalation",
        "escalate",
        "severity",
        "urgent",
        "p1",
        "sla",
        "critical",
        "high priority"
    ]

    if any(keyword in query_lower for keyword in escalation_keywords):
        return "escalation"

    # Ticket workflow
    ticket_keywords = [
        "ticket",
        "support request",
        "support case",
        "case status",
        "issue status"
    ]

    if any(keyword in query_lower for keyword in ticket_keywords):
        return "ticket"

    # Order / parcel workflow
    order_keywords = [
        "order",
        "parcel",
        "shipment",
        "delivery",
        "where is my parcel",
        "where is my order",
        "tracking",
        "pickup"
    ]

    if any(keyword in query_lower for keyword in order_keywords):
        return "order"

    # Account workflow
    account_keywords = [
        "account",
        "my plan",
        "support available",
        "premium support",
        "account status"
    ]

    if any(keyword in query_lower for keyword in account_keywords):
        return "account"

    # Default workflow
    return "general"

