"""Minimal Gradio interface for company search and equity research."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

import gradio as gr
import yfinance as yf

from .agents.orchestrator import stream_research_workflow
from .tools.common import validate_ticker

MAX_SEARCH_RESULTS = 10
DEFAULT_QUESTION = (
    "Prepare a balanced educational equity research brief. Include "
    "as-of dates, "
    "currencies, source URLs, and uncertainty/data caveats. Treat DCF only as "
    "an illustrative scenario with explicit assumptions and methodology limits."
)


def _search_choices(quotes: Iterable[dict]) -> list[tuple[str, str]]:
    """Convert Yahoo search records to display labels and workflow values."""
    choices = []
    seen_symbols = set()
    for item in quotes:
        if not isinstance(item, dict):
            continue
        quote_type = str(item.get("quoteType") or "").upper()
        if quote_type and quote_type != "EQUITY":
            continue
        symbol, error = validate_ticker(item.get("symbol"))
        if error or symbol is None or symbol in seen_symbols:
            continue
        company_name = str(
            item.get("longname") or item.get("shortname") or symbol
        ).strip()
        exchange = str(
            item.get("exchDisp") or item.get("exchange") or ""
        ).strip()
        label = f"{company_name} — {symbol}"
        if exchange:
            label += f" ({exchange})"
        choices.append((label, f"{symbol}\t{company_name}"))
        seen_symbols.add(symbol)
        if len(choices) >= MAX_SEARCH_RESULTS:
            break
    return choices


def search_companies(query: str | None) -> tuple[dict, str]:
    """Search Yahoo Finance for company names and return selectable results."""
    if not isinstance(query, str) or not query.strip():
        return (
            gr.update(choices=[], value=None),
            "Enter a company name to search.",
        )
    try:
        quotes = yf.Search(
            query.strip(),
            max_results=MAX_SEARCH_RESULTS,
            news_count=0,
            lists_count=0,
            include_cb=False,
            include_nav_links=False,
        ).quotes
    except Exception as exc:
        return (
            gr.update(choices=[], value=None),
            f"Company search failed ({type(exc).__name__}).",
        )

    choices = _search_choices(quotes or [])
    if not choices:
        return gr.update(choices=[], value=None), "No matching companies found."
    return (
        gr.update(choices=choices, value=None),
        f"Found {len(choices)} matching companies. Select one to continue.",
    )


async def run_selected_company(
    selection: str | None, research_question: str | None
) -> AsyncIterator[tuple[str, str, dict]]:
    """Run research and stream visible progress through the button state."""
    if not selection:
        yield (
            "Select a company from the search results first.",
            "",
            _button_update("Select a company", "stop", True),
        )
        return
    try:
        ticker, company_name = selection.split("\t", maxsplit=1)
    except ValueError:
        yield (
            "The selected company entry is invalid. Search and select again.",
            "",
            _button_update("Invalid selection", "stop", True),
        )
        return
    ticker, ticker_error = validate_ticker(ticker)
    if ticker_error or not company_name.strip():
        yield (
            "The selected company entry is invalid. Search and select again.",
            "",
            _button_update("Invalid selection", "stop", True),
        )
        return

    question = (research_question or "").strip() or DEFAULT_QUESTION
    request = f"Research {company_name} (ticker: {ticker}). {question}"
    yield (
        "Research is starting…",
        "",
        _button_update("Researching…", "secondary", False),
    )
    completed = False
    failed = False
    try:
        async for status, report in stream_research_workflow(request):
            if (
                status
                in {
                    "Research complete.",
                    "Research complete with deterministic fallback.",
                }
                and report
            ):
                completed = True
                label = (
                    "✓ Brief ready (fallback)"
                    if "fallback" in status
                    else "✓ Research complete"
                )
                yield (
                    status,
                    report,
                    _button_update(label, "primary", True),
                )
            elif status.startswith(
                (
                    "Workflow stopped",
                    "Research incomplete:",
                    "Workflow finished without",
                    "Report synthesis returned",
                )
            ):
                failed = True
                yield (
                    status,
                    report,
                    _button_update("Research failed", "stop", True),
                )
            else:
                yield (
                    status,
                    report,
                    _button_update("Researching…", "secondary", False),
                )
    except Exception as exc:
        yield (
            f"Workflow stopped ({type(exc).__name__}).",
            "",
            _button_update("Research failed", "stop", True),
        )
        return
    if not completed and not failed:
        yield (
            "Workflow ended without a completed research brief.",
            "",
            _button_update("Research failed", "stop", True),
        )


def _button_update(label: str, variant: str, interactive: bool) -> dict:
    """Build the visible and interactive state for the research button."""
    return gr.update(value=label, variant=variant, interactive=interactive)


def _reset_research_button() -> dict:
    """Restore the initial button after the next input edit."""
    return _button_update("Run research", "primary", True)


def create_app() -> gr.Blocks:
    """Build the UI without starting a server or calling data providers."""
    with gr.Blocks(title="Company Research Assistant") as app:
        gr.Markdown(
            "# Company Research Assistant\n"
            "Search for a company, choose the matching listing, and review "
            "an educational research brief."
        )
        with gr.Row():
            company_query = gr.Textbox(
                label="Company name",
                placeholder="e.g. Titan Company, Apple, Microsoft",
            )
            search_button = gr.Button("Search", variant="secondary")
        company_choices = gr.Dropdown(
            label="Select company",
            choices=[],
            value=None,
            allow_custom_value=True,
            interactive=True,
        )
        search_status = gr.Markdown()
        research_question = gr.Textbox(
            label="What would you like to know about this company?",
            value=DEFAULT_QUESTION,
            placeholder=(
                "For example: Summarize its financial health, key risks, "
                "and valuation."
            ),
            lines=3,
        )
        run_button = gr.Button("Run research", variant="primary")
        workflow_status = gr.Markdown()
        report = gr.Markdown(label="Research brief")

        # Gradio injects event methods dynamically; pylint cannot infer them.
        # pylint: disable=no-member
        search_button.click(
            search_companies,
            inputs=company_query,
            outputs=[company_choices, search_status],
        )
        company_query.submit(
            search_companies,
            inputs=company_query,
            outputs=[company_choices, search_status],
        )
        run_button.click(
            run_selected_company,
            inputs=[company_choices, research_question],
            outputs=[workflow_status, report, run_button],
        )
        company_choices.change(
            _reset_research_button,
            inputs=None,
            outputs=run_button,
            queue=False,
        )
        research_question.change(
            _reset_research_button,
            inputs=None,
            outputs=run_button,
            queue=False,
        )
        # pylint: enable=no-member
    return app


def main() -> None:
    """Start the local Gradio server."""
    create_app().queue().launch()
