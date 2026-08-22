from datetime import datetime


def create_escalation(ticket_id, reason):
    return {
        "success": True,
        "escalation_id": f"ESC-{ticket_id}",
        "ticket_id": ticket_id,
        "reason": reason,
        "status": "Escalation created",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }