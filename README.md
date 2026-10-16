# DataBridge

A LangChain agent connected to three different kinds of real systems at once: a SQL database, a live third-party REST API, and a legacy flat-file export. Ask it a question, and it decides for itself which system (or combination of systems) it needs to answer it.

## Why three different system types

Most real integration work isn't "connect to one clean API." It's some mix of a proper database, a couple of external services, and at least one old system that only exports a CSV because nobody has migrated it yet. This project is built around that mix on purpose:

- **Company database** (SQLite, standing in for something like Postgres or Snowflake) -- customers, products, orders, and order items.
- **Live exchange rate API** ([frankfurter.dev](https://frankfurter.dev), no key required) -- a genuine external network call, not a mock.
- **Legacy inventory export** (`data/legacy_inventory_export.csv`) -- warehouse stock data that predates the database and was never migrated into it, which is a very ordinary situation at real companies.

## How it decides what to use

The agent has four tools: `describe_database`, `run_sql_query`, `get_exchange_rate`, and `read_legacy_inventory_export`. Given a question, the model decides which tools it needs and in what order. A question like "what's the value of order 8 in euros" needs both the database (to find the order total) and the exchange rate API (to convert it) -- the agent has to sequence both correctly on its own, nothing in the code tells it "always call these two together."

The database side follows the standard text-to-SQL agent pattern: `describe_database` returns the schema first, then the model writes its own SQL based on that schema and runs it through `run_sql_query`. Nothing hardcodes what questions are answerable; the model composes the query itself.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Default provider is Ollama (fully local, free, no key). Set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` in `.env` to use a hosted model instead.

The database is created automatically the first time you run the agent (`setup_db.py`, called from `agent.py`) -- no manual setup step.

## Usage

```bash
python agent.py
```

Then ask it things like:

```
> Which customers are in the West region?
> What's the total value of order 8, and what would that be in EUR?
> How much Standing Desk stock is in the warehouse?
> Which products exist in the warehouse export but have never been ordered?
```

That last one needs the agent to cross-reference the legacy CSV against the database, since the two systems were never connected to each other until now.

## Design decisions

- **Read-only enforcement on SQL, in code, not just in the prompt.** `run_sql_query` rejects anything that isn't a `SELECT` before it ever reaches the database, regardless of what the model tries to run. Telling the model "only read data" in the system prompt is not the same guarantee as blocking write queries in code -- a model can still be talked into or accidentally generate a destructive query, so the actual safety boundary belongs in the tool, not the instructions.
- **Schema lookup as a separate tool from query execution.** Rather than one tool that takes a natural-language question and does everything internally, `describe_database` and `run_sql_query` are separate steps the model chains together itself. This mirrors how LangChain's own SQL toolkit is structured, and it means the model's reasoning about the schema is visible in the conversation rather than hidden inside a single tool call.
- **A real external API, not a mock.** `get_exchange_rate` calls a live, keyless public API rather than returning canned data, so the agent is actually handling a real network call, real response parsing, and a real failure path if the request fails.
- **The legacy system is deliberately disconnected from the database.** The CSV export and the SQL database don't share any foreign keys or join logic -- matching products between them (by name) is left to the model, the same way it would be at a company where two systems were never properly integrated.
- **Row cap on query results.** `run_sql_query` caps output at 50 rows so a broad query doesn't flood the model's context window; the tool tells the model how many rows were cut off rather than silently truncating.

## Future work

- Add a write-capable tool behind an explicit confirmation step, to demonstrate handling actions with real side effects safely rather than staying read-only everywhere.
- Swap the flat-file "legacy" system for something closer to a real legacy interface, like a SOAP endpoint or fixed-width file format.
- Add a second live API (e.g. a shipping/logistics lookup) to test how the agent handles three or more available tools with overlapping relevance.
