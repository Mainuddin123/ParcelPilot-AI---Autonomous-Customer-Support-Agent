from src.agent import ParcelPilotAgent


def main():

    agent = ParcelPilotAgent()

    print("=" * 55)
    print("📦 Welcome to ParcelPilot AI")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 55)

    while True:

        query = input("\nYou: ").strip()

        # =========================================
        # EXIT APPLICATION
        # =========================================

        if query.lower() in ["exit", "quit"]:

            print("\nThank you for using ParcelPilot AI.")
            break

        # =========================================
        # HANDLE ESCALATION CONFIRMATION
        # =========================================

        if agent.pending_escalation:

            result = agent.process(
                query=query
            )

        # =========================================
        # NORMAL REQUEST
        # =========================================

        else:

            account_id = input(
                "Account ID (optional): "
            ).strip()

            order_id = input(
                "Order ID (optional): "
            ).strip()

            ticket_id = input(
                "Ticket ID (optional): "
            ).strip()

            result = agent.process(
                query=query,
                account_id=account_id or None,
                order_id=order_id or None,
                ticket_id=ticket_id or None
            )

        # =========================================
        # DISPLAY RESPONSE
        # =========================================

        print("\n" + "=" * 55)
        print("ParcelPilot AI:")
        print("=" * 55)

        print(
            result.get(
                "answer",
                "No response generated."
            )
        )

        print(
            f"\nStatus: {result.get('status')}"
        )


if __name__ == "__main__":
    main()