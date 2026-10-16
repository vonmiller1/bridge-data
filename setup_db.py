"""
Creates and populates the sample SQLite database this project queries.

Standing in for a real company's order-management system: customers, products,
orders, order_items. Run automatically by agent.py on first launch if the
database file doesn't exist yet, so cloning the repo and running it just works
without a manual setup step.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "company.db")

SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

CUSTOMERS = [
    (1, "Aria Chen", "West", "2024-02-14"),
    (2, "Marcus Bell", "Midwest", "2024-03-01"),
    (3, "Priya Nair", "Northeast", "2024-03-22"),
    (4, "Devon Ruiz", "South", "2024-05-10"),
    (5, "Kayla Osei", "West", "2024-06-18"),
    (6, "Tom Fischer", "Midwest", "2024-08-02"),
    (7, "Layla Haddad", "Northeast", "2024-09-15"),
    (8, "Noah Petrov", "South", "2025-01-09"),
]

PRODUCTS = [
    (1, "Wireless Mouse", "Accessories", 24.99),
    (2, "Mechanical Keyboard", "Accessories", 89.99),
    (3, "27in Monitor", "Displays", 249.99),
    (4, "USB-C Dock", "Accessories", 64.99),
    (5, "Webcam 1080p", "Accessories", 39.99),
    (6, "Standing Desk", "Furniture", 349.99),
    (7, "Office Chair", "Furniture", 199.99),
]

ORDERS = [
    (1, 1, "2024-04-01", "delivered"),
    (2, 2, "2024-04-15", "delivered"),
    (3, 1, "2024-05-20", "delivered"),
    (4, 3, "2024-06-02", "delivered"),
    (5, 4, "2024-06-10", "cancelled"),
    (6, 5, "2024-07-01", "delivered"),
    (7, 2, "2024-08-14", "delivered"),
    (8, 6, "2024-09-01", "shipped"),
    (9, 7, "2024-10-05", "delivered"),
    (10, 1, "2024-11-11", "delivered"),
    (11, 8, "2025-01-20", "shipped"),
    (12, 3, "2025-02-02", "delivered"),
]

ORDER_ITEMS = [
    (1, 1, 1, 2), (2, 1, 2, 1), (3, 2, 3, 1), (4, 3, 4, 1),
    (5, 4, 3, 2), (6, 5, 6, 1), (7, 6, 1, 1), (8, 6, 5, 1),
    (9, 7, 2, 1), (10, 8, 6, 1), (11, 8, 7, 2), (12, 9, 3, 1),
    (13, 10, 1, 3), (14, 10, 4, 1), (15, 11, 7, 1), (16, 12, 2, 1),
    (17, 12, 5, 1),
]


def ensure_db_exists():
    """Create and populate the database if it doesn't already exist. Safe to
    call every time the agent starts -- does nothing if the file is already there."""
    if os.path.exists(DB_PATH):
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", CUSTOMERS)
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", PRODUCTS)
        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", ORDERS)
        conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", ORDER_ITEMS)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ensure_db_exists()
    print(f"Database ready at {DB_PATH}")
