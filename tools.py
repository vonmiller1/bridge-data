"""
Tools for the data integration agent. Each one stands in for a real category
of system this kind of agent commonly has to connect to:

- describe_database / run_sql_query -> a real database (SQLite here, same
  interface as Postgres/MySQL/Snowflake as far as the agent is concerned)
- get_exchange_rate -> a live third-party REST API
- read_legacy_inventory_export -> a "legacy system" that only produces flat
  files, which is a genuinely common integration pattern at real companies
  (nightly CSV/fixed-width dumps from a system nobody wants to touch)
"""

import csv
import os
import re
import sqlite3

import requests
from langchain_core.tools import tool

_FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|truncate)\b",
    re.IGNORECASE,
)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "company.db")
LEGACY_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "legacy_inventory_export.csv")
EXCHANGE_RATE_API = "https://api.frankfurter.dev/v1/latest"


@tool
def describe_database() -> str:
    """Return the schema of the company database: every table, its columns,
    and their types. Always call this before writing a SQL query if you
    haven't already seen the schema in this conversation -- guessing column
    names instead of checking is how text-to-SQL agents produce broken queries.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        lines = []
        for table in tables:
            safe_name = table.replace('"', '""')
            cursor.execute(f'PRAGMA table_info("{safe_name}")')
            columns = cursor.fetchall()
            col_desc = ", ".join(f"{col[1]} ({col[2]})" for col in columns)
            lines.append(f"{table}: {col_desc}")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def run_sql_query(query: str) -> str:
    """Run a read-only SQL query against the company database and return the
    results. Only SELECT statements are allowed -- anything else (INSERT,
    UPDATE, DELETE, DROP, etc.) is rejected before it ever reaches the
    database. Always call describe_database first so column/table names in
    the query are correct.
    """
    stripped = query.strip()
    if not stripped:
        return "Rejected: empty query."

    normalized = stripped.lower()
    if not normalized.startswith("select"):
        return (
            "Rejected: only SELECT queries are allowed through this tool. "
            "This agent has read-only access to the database by design."
        )
    if ";" in stripped:
        return "Rejected: multiple SQL statements are not allowed."
    if _FORBIDDEN_SQL.search(stripped):
        return (
            "Rejected: query contains disallowed keywords. "
            "Only read-only SELECT queries are permitted."
        )

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
    except sqlite3.Error as exc:
        return f"SQL error: {exc}. Check the schema with describe_database and try again."
    finally:
        conn.close()

    if not rows:
        return "Query ran successfully but returned no rows."

    header = " | ".join(columns)
    lines = [header, "-" * len(header)]
    for row in rows[:50]:  # cap output so one runaway query doesn't blow up the context window
        lines.append(" | ".join(str(v) for v in row))
    if len(rows) > 50:
        lines.append(f"... ({len(rows) - 50} more rows not shown)")
    return "\n".join(lines)


@tool
def get_exchange_rate(base_currency: str, target_currency: str) -> str:
    """Get the current exchange rate between two currencies using a live
    external API (no key required). Use 3-letter currency codes, e.g. USD, EUR, GBP, INR.
    """
    try:
        response = requests.get(
            EXCHANGE_RATE_API,
            params={"from": base_currency.upper(), "to": target_currency.upper()},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Could not fetch exchange rate: {exc}"

    rate = data.get("rates", {}).get(target_currency.upper())
    if rate is None:
        return f"No rate found for {base_currency} -> {target_currency}. Check the currency codes."
    return f"1 {base_currency.upper()} = {rate} {target_currency.upper()} (as of {data.get('date')})"


@tool
def read_legacy_inventory_export() -> str:
    """Read the legacy warehouse system's inventory export. This system is
    old enough that it only produces a flat CSV file on a schedule -- there's
    no API and no direct database access, which is common for systems
    companies haven't gotten around to modernizing. Returns stock counts by
    product and warehouse location.
    """
    if not os.path.exists(LEGACY_CSV_PATH):
        return f"No export file found at {LEGACY_CSV_PATH}."

    with open(LEGACY_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return "Export file is empty."

    header = " | ".join(rows[0].keys())
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(" | ".join(row.values()))
    return "\n".join(lines)


ALL_TOOLS = [describe_database, run_sql_query, get_exchange_rate, read_legacy_inventory_export]
