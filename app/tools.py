"""
Tool functions the agent can call. Each one talks to the SQLite database
and returns a plain dict (JSON-serializable) — never raw SQL rows.

Keep these functions small and single-purpose: this list IS the agent's
entire capability surface. Adding a feature to the agent means adding a
function here + a matching schema in tool_schemas.py, nothing else.
"""
import sqlite3
from datetime import date, timedelta

DB_PATH = "data/shop.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_sales_summary(start_date: str, end_date: str) -> dict:
    """Revenue and order volume between two dates (inclusive), plus top products."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT SUM(quantity * unit_price) as revenue, COUNT(*) as line_items,
                  SUM(quantity) as units_sold
           FROM sales WHERE date BETWEEN ? AND ?""",
        (start_date, end_date),
    )
    row = cur.fetchone()

    cur.execute(
        """SELECT product_name, SUM(quantity) as units, SUM(quantity * unit_price) as revenue
           FROM sales WHERE date BETWEEN ? AND ?
           GROUP BY product_name ORDER BY revenue DESC LIMIT 3""",
        (start_date, end_date),
    )
    top = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "revenue": round(row["revenue"] or 0, 2),
        "units_sold": row["units_sold"] or 0,
        "line_items": row["line_items"] or 0,
        "top_products": top,
    }


def get_low_stock_items(threshold: int = None) -> dict:
    """Items at or below their reorder threshold (or a custom threshold if given)."""
    conn = _conn()
    cur = conn.cursor()
    if threshold is not None:
        cur.execute(
            "SELECT sku, product_name, quantity_on_hand, reorder_threshold, supplier "
            "FROM inventory WHERE quantity_on_hand <= ? ORDER BY quantity_on_hand ASC",
            (threshold,),
        )
    else:
        cur.execute(
            "SELECT sku, product_name, quantity_on_hand, reorder_threshold, supplier "
            "FROM inventory WHERE quantity_on_hand <= reorder_threshold ORDER BY quantity_on_hand ASC"
        )
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(items), "items": items}


def get_top_selling_products(period_days: int = 30, limit: int = 5) -> dict:
    """Best-selling products (by revenue) over the last N days."""
    start = (date.today() - timedelta(days=period_days)).isoformat()
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT product_name, SUM(quantity) as units, SUM(quantity * unit_price) as revenue
           FROM sales WHERE date >= ?
           GROUP BY product_name ORDER BY revenue DESC LIMIT ?""",
        (start, limit),
    )
    products = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"period_days": period_days, "products": products}


def get_product_details(sku: str) -> dict:
    """Current stock + recent sales history for a single SKU."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
    inv_row = cur.fetchone()
    if not inv_row:
        conn.close()
        return {"error": f"No product found with SKU '{sku}'"}

    cur.execute(
        """SELECT SUM(quantity) as units_last_30d, SUM(quantity * unit_price) as revenue_last_30d
           FROM sales WHERE sku = ? AND date >= ?""",
        (sku, (date.today() - timedelta(days=30)).isoformat()),
    )
    sales_row = cur.fetchone()
    conn.close()

    result = dict(inv_row)
    result["units_last_30d"] = sales_row["units_last_30d"] or 0
    result["revenue_last_30d"] = round(sales_row["revenue_last_30d"] or 0, 2)
    return result


def update_stock_level(sku: str, new_quantity: int, reason: str, confirm: bool = False) -> dict:
    """
    Adjusts inventory for a SKU. Requires confirm=true to actually write —
    call it first with confirm=false (or omitted) to get a confirmation
    message, then call it again with confirm=true once the owner agrees.
    This two-step pattern is what keeps a write-capable agent safe.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT product_name, quantity_on_hand FROM inventory WHERE sku = ?", (sku,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": f"No product found with SKU '{sku}'"}

    if not confirm:
        conn.close()
        return {
            "status": "confirmation_required",
            "message": (
                f"About to change {row['product_name']} ({sku}) stock from "
                f"{row['quantity_on_hand']} to {new_quantity}. Reason: {reason}. "
                f"Call update_stock_level again with confirm=true to proceed."
            ),
        }

    cur.execute(
        "UPDATE inventory SET quantity_on_hand = ?, last_restocked = ? WHERE sku = ?",
        (new_quantity, date.today().isoformat(), sku),
    )
    conn.commit()
    conn.close()
    return {
        "status": "updated",
        "sku": sku,
        "product_name": row["product_name"],
        "previous_quantity": row["quantity_on_hand"],
        "new_quantity": new_quantity,
        "reason": reason,
    }


TOOL_MAP = {
    "get_sales_summary": get_sales_summary,
    "get_low_stock_items": get_low_stock_items,
    "get_top_selling_products": get_top_selling_products,
    "get_product_details": get_product_details,
    "update_stock_level": update_stock_level,
}
