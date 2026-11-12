
import pandas as pd

from src.data_loader import DataLoader
from src.config import DATASET_SNAPSHOT
from src.database import execute_cancellation


data = DataLoader()


def check_cancellation(order_id: str, account_id: str = None):
    """Check cancellation eligibility without changing order data."""

    order = data.get_order(order_id)

    if order is None:
        return {
            "found": False,
            "allowed": False,
            "can_cancel": False,
            "message": f"Order {order_id} was not found."
        }

    if account_id and str(order["account_id"]).upper() != str(account_id).upper():
        return {
            "found": False,
            "allowed": False,
            "can_cancel": False,
            "message": "Order does not belong to the selected account."
        }

    if order["status"] in {"DELIVERED", "CANCELLED"}:
        return {
            "found": True,
            "allowed": False,
            "can_cancel": False,
            "reason": f"Order status is {order['status']}.",
            "order": order
        }

    if pd.notna(order.get("pickup_actual_at")):
        return {
            "found": True,
            "allowed": False,
            "can_cancel": False,
            "reason": "The shipment has already been picked up.",
            "order": order
        }

    if pd.isna(order.get("cancellation_requested_at")):
        return {
            "found": True,
            "allowed": False,
            "can_cancel": False,
            "reason": "No cancellation request was found.",
            "order": order
        }

    return {
        "found": True,
        "allowed": True,
        "can_cancel": True,
        "reason": (
            "The shipment is still eligible for cancellation "
            "under the applicable customer agreement."
        ),
        "order_id": order_id,
        "account_id": order["account_id"],
        "cancellation_requested_at": str(
            order["cancellation_requested_at"]
        ),
        "dataset_snapshot": str(DATASET_SNAPSHOT)
    }


def cancel_order(order_id: str, account_id: str):
    """Execute cancellation after explicit customer confirmation."""

    return execute_cancellation(order_id, account_id)
