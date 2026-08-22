import pandas as pd

from src.config import EXCEL_FILE


class DataLoader:

    def __init__(self):

        self.accounts = pd.read_excel(
            EXCEL_FILE,
            sheet_name="accounts"
        )

        self.orders = pd.read_excel(
            EXCEL_FILE,
            sheet_name="orders"
        )

        self.tickets = pd.read_excel(
            EXCEL_FILE,
            sheet_name="tickets"
        )

        # =========================================
        # CLEAN COLUMN NAMES
        # =========================================

        self.accounts.columns = (
            self.accounts.columns.astype(str)
            .str.strip()
        )

        self.orders.columns = (
            self.orders.columns.astype(str)
            .str.strip()
        )

        self.tickets.columns = (
            self.tickets.columns.astype(str)
            .str.strip()
        )

        # =========================================
        # NORMALIZE ID COLUMNS
        # =========================================

        self._normalize_id_column(
            self.accounts,
            "account_id"
        )

        self._normalize_id_column(
            self.orders,
            "order_id"
        )

        self._normalize_id_column(
            self.orders,
            "account_id"
        )

        self._normalize_id_column(
            self.tickets,
            "ticket_id"
        )

        self._normalize_id_column(
            self.tickets,
            "account_id"
        )

    # =============================================
    # NORMALIZE ID VALUES
    # =============================================

    def _normalize_id_column(
        self,
        dataframe,
        column
    ):

        if column in dataframe.columns:

            dataframe[column] = (
                dataframe[column]
                .astype(str)
                .str.strip()
                .str.upper()
            )

    # =============================================
    # GET ACCOUNT
    # =============================================

    def get_account(
        self,
        account_id
    ):

        if not account_id:
            return None

        account_id = (
            str(account_id)
            .strip()
            .upper()
        )

        result = self.accounts[
            self.accounts["account_id"]
            == account_id
        ]

        if result.empty:
            return None

        return result.iloc[0].to_dict()

    # =============================================
    # GET ORDER
    # =============================================

    def get_order(
        self,
        order_id
    ):

        if not order_id:
            return None

        order_id = (
            str(order_id)
            .strip()
            .upper()
        )

        result = self.orders[
            self.orders["order_id"]
            == order_id
        ]

        if result.empty:
            return None

        return result.iloc[0].to_dict()

    # =============================================
    # GET TICKET
    # =============================================

    def get_ticket(
        self,
        ticket_id
    ):

        if not ticket_id:
            return None

        ticket_id = (
            str(ticket_id)
            .strip()
            .upper()
        )

        result = self.tickets[
            self.tickets["ticket_id"]
            == ticket_id
        ]

        if result.empty:
            return None

        return result.iloc[0].to_dict()

    # =============================================
    # GET ACCOUNT ORDERS
    # =============================================

    def get_account_orders(
        self,
        account_id
    ):

        if not account_id:
            return []

        account_id = (
            str(account_id)
            .strip()
            .upper()
        )

        result = self.orders[
            self.orders["account_id"]
            == account_id
        ]

        return result.to_dict(
            orient="records"
        )

    # =============================================
    # GET ACCOUNT TICKETS
    # =============================================

    def get_account_tickets(
        self,
        account_id
    ):

        if not account_id:
            return []

        account_id = (
            str(account_id)
            .strip()
            .upper()
        )

        result = self.tickets[
            self.tickets["account_id"]
            == account_id
        ]

        return result.to_dict(
            orient="records"
        )