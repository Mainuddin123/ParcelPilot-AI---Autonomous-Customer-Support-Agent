import pandas as pd

from src.data_loader import DataLoader
from src.config import DATASET_SNAPSHOT


data = DataLoader()


def check_cancellation(order_id: str):
    """
    Check whether an order can potentially be cancelled.
    This only makes a decision; it does not change any data.
    """

    order = data.get_order(order_id)

    if order is None:
        return {
            "found": False,
            "message": f"Order {order_id} was not found."
        }

    # Cannot cancel an already completed shipment
    if order["status"] == "DELIVERED":
        return {
            "found": True,
            "allowed": False,
            "can_cancel": False,
            "reason": "The shipment has already been delivered.",
            "order": order
        }

    # If pickup already happened, cancellation requires further handling
    if pd.notna(order["pickup_actual_at"]):
        return {
            "found": True,
            "can_cancel": False,
            "reason": "The shipment has already been picked up.",
            "order": order
        }

    # Cancellation request must exist
    if pd.isna(order["cancellation_requested_at"]):
        return {
            "found": True,
            "can_cancel": False,
            "reason": "No cancellation request was found.",
            "order": order
        }

    snapshot_time = pd.Timestamp(DATASET_SNAPSHOT)
    request_time = pd.Timestamp(order["cancellation_requested_at"])

    return {
        "found": True,
        "allowed": True,
        "can_cancel": True,
        "reason": "The shipment is still BOOKED and pickup has not been recorded. Under the Northstar Logistics customer-specific agreement shown for this account, cancellation before pickup is permitted without a cancellation fee.",
        "order_id": order_id,
        "account_id": order["account_id"],
        "cancellation_requested_at": request_time.strftime(
            "%Y-%m-%d %H:%M"
        ),
        "dataset_snapshot": snapshot_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    }