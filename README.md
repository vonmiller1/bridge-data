# DataBridge

LangChain agent that answers natural-language questions by combining a SQLite company database, a live exchange-rate API, and a legacy warehouse CSV export.

## Overview

DataBridge demonstrates multi-system integration: the model chooses among four tools (`describe_database`, `run_sql_query`, `get_exchange_rate`, `read_legacy_inventory_export`) and chains them when a question spans systems—for example, order totals from SQL plus EUR conversion from [Frankfurter](https://frankfurter.dev). The sample schema mirrors a small order-management domain; the legacy CSV is intentionally not linked to the database, so cross-system questions rely on the agent matching product names.

## Features

- Text-to-SQL over a read-only SQLite schema (customers, products, orders, order items)
- Schema introspection before query execution
- Live currency conversion via Frankfurter (no API key)
- Legacy flat-file inventory read from `data/legacy_inventory_export.csv`
- Pluggable LLM backends: local Ollama (default), OpenAI, or Google Gemini

## Tech stack

- Python 3.10+
- [LangChain](https://python.langchain.com/) (`langchain`, `langchain-core`) with provider packages for Ollama, OpenAI, and Gemini
- SQLite (stdlib), `requests`, `python-dotenv`

## Prerequisites

- Python 3.10 or newer
- For default local inference: [Ollama](https://ollama.com/) with a model such as `llama3.2`
- For hosted models: API keys in the environment (see Configuration)

## Getting started

```bash
git clone https://github.com/vonmiller1/bridge-data.git
cd bridge-data
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` if you want a non-default LLM provider or model name.

## Running locally

```bash
python agent.py
```

On first run, `setup_db.py` creates `data/company.db` if it is missing. Type questions at the `>` prompt; enter `quit` or `exit` to leave.

Example prompts:

- Which customers are in the West region?
- What is the total value of order 8, and what would that be in EUR?
- How much Standing Desk stock is in the warehouse?
- Which products appear in the warehouse export but have never been ordered?

## Testing

This repository does not ship an automated test suite. After changes, run `python agent.py` and exercise the sample prompts above manually.

## Project structure

| Path | Role |
|------|------|
| `agent.py` | CLI entrypoint; builds the LangChain agent and REPL loop |
| `models.py` | Selects chat model from `LLM_PROVIDER` |
| `tools.py` | Database, exchange-rate, and legacy CSV tools |
| `setup_db.py` | Creates and seeds `data/company.db` |
| `data/company.db` | Sample SQLite database (created on first run if absent) |
| `data/legacy_inventory_export.csv` | Legacy warehouse export |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `openai`, or `gemini` |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model tag when using Ollama |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `GEMINI_API_KEY` | — | Required when `LLM_PROVIDER=gemini` |

Do not commit real API keys; keep them in `.env` only.

## Deployment

No Dockerfile or CI workflow is included. Run on any host with Python, network access (for hosted LLMs and Frankfurter), and optional Ollama for local models.

## Contributing

Fork the repository, create a feature branch, and use clear commit messages. Open a pull request with a short description of behavior and any security-sensitive changes.

## License

No `LICENSE` file is present in this repository; add one before distributing or reusing the code commercially.
