from src.data_loader import DataLoader


data = DataLoader()


def detect_order_issues(order: dict):
    """
    Detect important order issues automatically.
    """

    issues = []

    status = str(
        order.get("status", "")
    ).lower()

    pickup_actual = order.get(
        "pickup_actual_at"
    )

    pickup_end = order.get(
        "pickup_window_end"
    )

    # Delayed order indicators
    if "delayed" in status:
        issues.append(
            "The order is currently delayed."
        )

    # Pickup issue
    if (
        pickup_end
        and (
            pickup_actual is None
            or str(pickup_actual).lower() == "nan"
        )
        and "picked" not in status
        and "delivered" not in status
    ):
        issues.append(
            "The scheduled pickup has not yet been recorded."
        )

    # Cancellation-related warning
    if any(
        keyword in status
        for keyword in [
            "cancelled",
            "canceled"
        ]
    ):
        issues.append(
            "This order has already been cancelled."
        )

    return issues


def lookup_order(
    order_id: str,
    account_id: str = None
):
    """
    Fetch an order, verify ownership,
    and proactively detect issues.
    """

    if not account_id:
        return {
            "found": False,
            "message": "An Account ID is required to verify order ownership."
        }

    order = data.get_order(order_id)

    if order is None:
        return {
            "found": False,
            "message": f"Order {order_id} was not found."
        }

    # Customer data isolation
    if (
        account_id
        and order.get("account_id") != account_id
    ):
        return {
            "found": False,
            "message": (
                "Access denied: this order does not belong "
                "to the provided account."
            )
        }

    # Proactively detect order issues
    issues = detect_order_issues(order)

    return {
        "found": True,
        "order": order,
        "issues": issues,
        "issue_detected": len(issues) > 0
    }


def lookup_account(account_id: str):
    """
    Fetch account details using an account ID.
    """

    account = data.get_account(account_id)

    if account is None:
        return {
            "found": False,
            "message": f"Account {account_id} was not found."
        }

    return {
        "found": True,
        "account": account
    }