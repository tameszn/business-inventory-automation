"""
OpenAI-format function-calling schemas — one per function in tools.py.
This is the model's menu of capabilities; it never sees your Python code,
only these descriptions and parameter definitions.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Get total revenue, units sold, and top products for a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD, inclusive"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD, inclusive"},
                },
                "required": ["start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_items",
            "description": "List inventory items at or below their reorder threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Optional custom threshold; if omitted, uses each item's own reorder threshold.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_selling_products",
            "description": "Get the best-selling products by revenue over the last N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period_days": {"type": "integer", "description": "Lookback window in days, e.g. 7 or 30"},
                    "limit": {"type": "integer", "description": "How many products to return"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get current stock level and recent sales history for one SKU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "The product SKU, e.g. SKU-004"},
                },
                "required": ["sku"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock_level",
            "description": (
                "Change the recorded stock quantity for a SKU. Always call this first with "
                "confirm=false to preview the change, show the owner the confirmation message, "
                "and only call it again with confirm=true after the owner explicitly agrees."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string"},
                    "new_quantity": {"type": "integer"},
                    "reason": {"type": "string", "description": "Why the stock is changing, e.g. 'restocked from supplier'"},
                    "confirm": {"type": "boolean", "description": "Set true only after the owner has confirmed."},
                },
                "required": ["sku", "new_quantity", "reason"],
            },
        },
    },
]
