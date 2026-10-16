"""
Data Integration Agent -- a LangChain agent connected to three different
kinds of real systems: a SQL database, a live external REST API, and a
legacy flat-file export. Ask it a question that needs any combination of
these, and it decides which tool(s) to call and in what order.

Usage:
    python agent.py
    (then type a question)
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent

from models import build_chat_model
from setup_db import ensure_db_exists
from tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are a data integration assistant with access to three different \
systems:

1. A company database (tools: describe_database, run_sql_query) -- customers, products, \
orders, and order_items. Always call describe_database first if you haven't already seen \
the schema, so you don't guess at table or column names. Only SELECT queries are allowed.
2. A live currency exchange rate API (tool: get_exchange_rate) -- for converting monetary \
values between currencies using current rates.
3. A legacy warehouse inventory system (tool: read_legacy_inventory_export) -- this system \
predates the company database and only produces a CSV export. It has no API and isn't \
in the SQL database, so if a question is about warehouse stock levels, use this tool, not \
the database.

Combine tools when a question needs it -- for example, a question about the dollar value of \
an order in another currency needs both the database and the exchange rate API. Always base \
your answer on the actual tool outputs, not on assumptions about what the data probably says. \
If a question can't be answered with the tools available, say so plainly instead of guessing."""


def run():
    ensure_db_exists()

    model = build_chat_model()
    agent = create_agent(model=model, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT)

    print("Data Integration Agent (LangChain)")
    print(f"Provider: {os.environ.get('LLM_PROVIDER', 'ollama')}")
    print("Connected systems: company database (SQLite), live exchange rate API, legacy inventory CSV")
    print("-" * 60)
    print("Ask a question (or type 'quit' to exit).")
    print("Try: 'Which customers are in the West region?' or")
    print("     'What's the total value of order 8, and what would that be in EUR?' or")
    print("     'How much Standing Desk stock is in the warehouse?'")
    print()

    while True:
        question = input("> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        print()
        print(result["messages"][-1].content)
        print()


if __name__ == "__main__":
    run()
