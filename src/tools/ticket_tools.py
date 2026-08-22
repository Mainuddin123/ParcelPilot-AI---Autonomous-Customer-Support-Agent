from src.data_loader import DataLoader


data = DataLoader()


def lookup_ticket(
    ticket_id: str,
    account_id: str = None
):
    """
    Fetch ticket details and verify that the ticket
    belongs to the provided account.
    """

    ticket = data.get_ticket(ticket_id)

    if ticket is None:
        return {
            "found": False,
            "reason": "Ticket not found"
        }

    # Customer data isolation
    if (
        account_id
        and ticket.get("account_id") != account_id
    ):
        return {
            "found": False,
            "reason": (
                "Access denied: this ticket does not belong "
                "to the provided account."
            )
        }

    return {
        "found": True,
        "ticket": ticket
    }