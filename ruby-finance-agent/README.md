# Ruby Finance Agent

An educational equity research project organized as an installable Python
package. Specialist agents and their data tools live under
`src/ruby_finance_agent/`.

## Setup

Requires Python 3.14 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Set `OPENAI_API_KEY` in the environment before running a research workflow.
News retrieval uses the configured FMP key when available and can fall back to
Yahoo Finance. Do not commit `.env`.

## Run

```bash
uv run ruby-finance-agent "AAPL outlook"
```

The current package entry point connects the command to the orchestrated
workflow. To use the web interface, run:

```bash
uv run ruby-finance-agent-ui
```

Search for a company by name, select a ticker from the results, and start the
research workflow. Company search requires an internet connection. Workflow
progress appears as graph nodes finish; the final report includes linked
citations where source URLs are available.

All generated research is educational and is not financial advice.
