from src.data_loader import DataLoader


data = DataLoader()


def check_service_credit(order_id: str):
    order = data.get_order(order_id)

    if not order:
        return {
            "found": False,
            "reason": "Order not found"
        }

    carrier_fault = order.get("carrier_fault")
    shipment_fee = order.get("shipment_fee_inr", 0)

    if carrier_fault:
        return {
            "found": True,
            "eligible": True,
            "credit_amount_inr": shipment_fee,
            "reason": (
                "Carrier fault is present. "
                "The shipment fee may be credited "
                "subject to the applicable agreement and SOP."
            )
        }

    return {
        "found": True,
        "eligible": False,
        "credit_amount_inr": 0,
        "reason": "Carrier fault is not present."
    }