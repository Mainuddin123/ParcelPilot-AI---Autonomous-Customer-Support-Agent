
import sqlite3
import pandas as pd

from src.config import EXCEL_FILE, DATASET_SNAPSHOT


DB_FILE = "parcelpilot.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create and seed SQLite tables from Excel on first run."""

    conn = get_connection()

    try:
        for sheet, table in [
            ("accounts", "accounts"),
            ("orders", "orders"),
            ("tickets", "tickets"),
        ]:
            exists = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=?",
                (table,)
            ).fetchone()

            if not exists:
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                df.columns = df.columns.astype(str).str.strip()

                for column in df.columns:
                    if column.endswith("_id"):
                        df[column] = (
                            df[column].astype(str).str.strip().str.upper()
                        )

                df.to_sql(table, conn, if_exists="replace", index=False)

        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN cancellation_status TEXT DEFAULT 'NOT_CANCELLED'
        """) if "cancellation_status" not in {
            row["name"] for row in conn.execute("PRAGMA table_info(orders)")
        } else None

        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN cancelled_at TEXT
        """) if "cancelled_at" not in {
            row["name"] for row in conn.execute("PRAGMA table_info(orders)")
        } else None

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cancellation_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(order_id, action)
            )
        """)

        conn.commit()

    finally:
        conn.close()

def load_table(table_name):
    """Load an existing SQLite table into a Pandas DataFrame."""

    allowed_tables = {"accounts", "orders", "tickets"}

    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    conn = get_connection()

    try:
        return pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn
        )
    finally:
        conn.close()

def get_order(order_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE UPPER(order_id) = ?",
            (str(order_id).strip().upper(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute_cancellation(order_id, account_id):
    """
    Atomically cancel an eligible order and record the action.
    Returns a structured result; never silently reports success.
    """

    order_id = str(order_id).strip().upper()
    account_id = str(account_id).strip().upper()

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        order = conn.execute(
            """
            SELECT * FROM orders
            WHERE UPPER(order_id) = ?
              AND UPPER(account_id) = ?
            """,
            (order_id, account_id)
        ).fetchone()

        if not order:
            conn.rollback()
            return {
                "success": False,
                "message": "Order not found for this account."
            }

        order = dict(order)

        if order.get("status") == "DELIVERED":
            conn.rollback()
            return {
                "success": False,
                "message": "Delivered shipments cannot be cancelled."
            }

        if order.get("pickup_actual_at") is not None:
            conn.rollback()
            return {
                "success": False,
                "message": "Shipment has already been picked up."
            }

        if order.get("cancellation_requested_at") is None:
            conn.rollback()
            return {
                "success": False,
                "message": "No cancellation request was found."
            }

        if order.get("cancellation_status") == "CANCELLED":
            conn.rollback()
            return {
                "success": False,
                "message": "This order has already been cancelled."
            }

        now = pd.Timestamp.now(tz="UTC").isoformat()

        cursor = conn.execute(
            """
            UPDATE orders
            SET status = 'CANCELLED',
                cancellation_status = 'CANCELLED',
                cancelled_at = ?
            WHERE UPPER(order_id) = ?
              AND UPPER(account_id) = ?
              AND status != 'DELIVERED'
              AND cancellation_status != 'CANCELLED'
            """,
            (now, order_id, account_id)
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "message": "Cancellation could not be completed. Please recheck the order."
            }

        conn.execute(
            """
            INSERT INTO cancellation_audit
                (order_id, account_id, action, reason, created_at)
            VALUES (?, ?, 'CANCELLED', ?, ?)
            """,
            (
                order_id,
                account_id,
                "Customer confirmed cancellation",
                now
            )
        )

        conn.commit()

        return {
            "success": True,
            "order_id": order_id,
            "account_id": account_id,
            "status": "CANCELLED",
            "cancelled_at": now,
            "message": f"Order {order_id} has been cancelled successfully."
        }

    except sqlite3.IntegrityError:
        conn.rollback()
        return {
            "success": False,
            "message": "A cancellation record already exists for this order."
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


initialize_database()
