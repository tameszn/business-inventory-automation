"""
Generates a realistic-ish synthetic SQLite database for the productivity agent
to operate on: a `sales` table and an `inventory` table for a small shop.

Run this once before starting the app:
    python data/generate_data.py
"""
import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "data/shop.db"

PRODUCTS = [
    ("SKU-001", "Cotton T-Shirt",      250, "Suraj Textiles"),
    ("SKU-002", "Denim Jeans",         900, "Suraj Textiles"),
    ("SKU-003", "Leather Wallet",      600, "Craftline Goods"),
    ("SKU-004", "Canvas Backpack",    1200, "Craftline Goods"),
    ("SKU-005", "Wireless Earbuds",   1800, "TechSource Imports"),
    ("SKU-006", "Phone Case",          300, "TechSource Imports"),
    ("SKU-007", "Ceramic Mug",         180, "Home & Hearth Co"),
    ("SKU-008", "Scented Candle",      220, "Home & Hearth Co"),
]

CUSTOMERS = [
    "Walk-in", "Priya S.", "Rahul M.", "Anita K.", "Vikram T.",
    "Sneha R.", "Amit D.", "Neha P.", "Walk-in", "Walk-in",
]


def build_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS sales")
    cur.execute("DROP TABLE IF EXISTS inventory")

    cur.execute("""
        CREATE TABLE sales (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sku TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            customer TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE inventory (
            sku TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            quantity_on_hand INTEGER NOT NULL,
            reorder_threshold INTEGER NOT NULL,
            supplier TEXT NOT NULL,
            last_restocked TEXT NOT NULL
        )
    """)

    # Seed starting stock, sized so a few items will realistically dip
    # below their reorder threshold once sales are applied.
    starting_stock = {
        "SKU-001": 80, "SKU-002": 40, "SKU-003": 35, "SKU-004": 25,
        "SKU-005": 20, "SKU-006": 60, "SKU-007": 50, "SKU-008": 45,
    }
    reorder_threshold = {
        "SKU-001": 20, "SKU-002": 10, "SKU-003": 10, "SKU-004": 8,
        "SKU-005": 8,  "SKU-006": 15, "SKU-007": 12, "SKU-008": 12,
    }

    today = date.today()
    start_day = today - timedelta(days=119)  # ~4 months of history

    # These two SKUs deliberately run low near "today" (supplier delay),
    # so the low-stock tool has something real to surface. Everything
    # else gets restocked normally when it dips below threshold.
    PROBLEM_SKUS = {"SKU-004", "SKU-005"}
    STOP_RESTOCKING_DAYS_AGO = 20  # problem SKUs stop being restocked this recently

    stock = dict(starting_stock)
    last_restocked = {sku: start_day.isoformat() for sku, *_ in PRODUCTS}

    day = start_day
    while day <= today:
        weekend_bump = 1.4 if day.weekday() >= 5 else 1.0
        days_from_today = (today - day).days

        for sku, name, price, supplier in PRODUCTS:
            base_chance = 0.55
            if random.random() < base_chance and stock.get(sku, 0) > 0:
                qty = max(1, int(random.gauss(2, 1) * weekend_bump))
                qty = min(qty, stock[sku])
                if qty > 0:
                    cur.execute(
                        "INSERT INTO sales (date, sku, product_name, quantity, unit_price, customer) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (day.isoformat(), sku, name, qty, price, random.choice(CUSTOMERS)),
                    )
                    stock[sku] -= qty

            # Restocking logic: refill when below threshold, unless this
            # is a problem SKU within the final stretch before "today".
            skip_restock = sku in PROBLEM_SKUS and days_from_today <= STOP_RESTOCKING_DAYS_AGO
            if stock.get(sku, 0) <= reorder_threshold[sku] and not skip_restock:
                stock[sku] = starting_stock[sku]
                last_restocked[sku] = day.isoformat()

        day += timedelta(days=1)

    for sku, name, price, supplier in PRODUCTS:
        cur.execute(
            "INSERT INTO inventory (sku, product_name, quantity_on_hand, reorder_threshold, supplier, last_restocked) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sku, name, max(stock.get(sku, 0), 0), reorder_threshold[sku], supplier, last_restocked[sku]),
        )

    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(PRODUCTS)} products and ~120 days of sales history.")


if __name__ == "__main__":
    build_db()
