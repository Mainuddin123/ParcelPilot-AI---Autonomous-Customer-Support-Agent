
import pandas as pd

from src.database import (
    initialize_database,
    load_table,
    get_order as get_sqlite_order,
)


class DataLoader:

    def __init__(self):

        # Initialize SQLite and migrate Excel data on first run
        initialize_database()

        # =========================================
        # LOAD DATA
        # =========================================

        self.accounts = pd.read_excel(
            __import__("src.config", fromlist=["EXCEL_FILE"]).EXCEL_FILE,
            sheet_name="accounts"
        )

        self.orders = load_table("orders")

        self.tickets = pd.read_excel(
            __import__("src.config", fromlist=["EXCEL_FILE"]).EXCEL_FILE,
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
    # GET ORDER - SQLITE
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

        return get_sqlite_order(order_id)

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
    # GET ACCOUNT ORDERS - SQLITE
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

    # =============================================
    # REFRESH ORDERS AFTER DATABASE UPDATE
    # =============================================

    def refresh_orders(self):

        self.orders = load_table("orders")

        self.orders.columns = (
            self.orders.columns.astype(str)
            .str.strip()
        )

        self._normalize_id_column(
            self.orders,
            "order_id"
        )

        self._normalize_id_column(
            self.orders,
            "account_id"
        )
