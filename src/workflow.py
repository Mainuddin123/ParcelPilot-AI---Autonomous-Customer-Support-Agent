def detect_workflow(query: str):
    q = query.lower().strip()

    cancellation = [
        "can i cancel", "cancel my order", "cancel order",
        "cancel shipment", "cancel my shipment", "cancel my parcel",
        "i want to cancel", "please cancel", "stop shipment",
        "stop my parcel", "request cancellation"
    ]
    if any(k in q for k in cancellation):
        return "cancellation"

    service_credit = [
        "service credit", "credit eligibility", "eligible for credit",
        "eligible for compensation", "claim compensation",
        "request compensation", "claim refund", "request a refund",
        "delivery compensation"
    ]
    if any(k in q for k in service_credit):
        return "service_credit"

    escalation_actions = [
        "escalate ticket", "escalate my ticket", "escalate my issue",
        "escalate this issue", "escalate this ticket",
        "i want to escalate", "please escalate", "raise an escalation",
        "raise escalation", "create an escalation", "create escalation",
        "submit an escalation", "submit escalation",
        "mark as urgent", "mark this as priority"
    ]
    if any(k in q for k in escalation_actions):
        return "escalation"

    # Information requests about policies should use RAG, not create actions.
    policy_terms = [
        "policy", "policies", "sla", "sop", "terms and conditions",
        "escalation process", "cancellation rules", "refund rules",
        "service credit rules"
    ]
    if any(k in q for k in policy_terms):
        return "general"

    if any(k in q for k in ["ticket status", "check ticket", "ticket details",
                            "support request status", "support case",
                            "case status", "issue status"]):
        return "ticket"

    if any(k in q for k in ["order", "parcel", "shipment", "delivery",
                            "tracking", "pickup"]):
        return "order"

    if any(k in q for k in ["account", "my plan", "support available",
                            "premium support", "account status"]):
        return "account"

    return "general"
