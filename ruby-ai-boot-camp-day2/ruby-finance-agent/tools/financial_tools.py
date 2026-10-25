"""Financial statement and operating metrics for the finance agent."""

import json
import math
import os
import ssl
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yfinance as yf
import certifi
from agents import function_tool


def _value(data: dict, key: str) -> object:
    value = data.get(key)
    if value is None:
        return None
    return value


def _format(value: object, *, money: bool = False, percent: bool = False) -> str:
    if value is None or isinstance(value, bool):
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if not math.isfinite(number):
        return "N/A"
    if percent:
        return f"{number * 100:.2f}%"
    return f"${number:,.2f}" if money else f"{number:,.2f}"


def _latest_statement_value(statement, label: str) -> object:
    """Return the newest available value for a financial-statement line item."""
    if statement is None or statement.empty or label not in statement.index:
        return None
    row = statement.loc[label].dropna()
    return row.iloc[0] if not row.empty else None


@function_tool
def get_company_financials(symbol: str) -> str:
    """Get recent financial performance and operating metrics from Yahoo Finance.

    Args:
        symbol: Yahoo Finance ticker, such as AAPL, TSLA, or TITAN.NS.

    Returns:
        Revenue, earnings, cash flow, debt, profitability, and growth metrics.
    """
    ticker = symbol.strip().upper()
    if not ticker:
        return "Please provide a stock ticker symbol."

    try:
        company = yf.Ticker(ticker)
        info = company.info
        if not info:
            return f"No financial data found for {ticker}."

        income = company.income_stmt
        balance = company.balance_sheet
        cash_flow = company.cashflow
        name = info.get("longName") or info.get("shortName") or ticker

        revenue = _latest_statement_value(income, "Total Revenue") or info.get("totalRevenue")
        net_income = _latest_statement_value(income, "Net Income") or info.get("netIncomeToCommon")
        operating_cash_flow = _latest_statement_value(
            cash_flow, "Operating Cash Flow"
        ) or info.get("operatingCashflow")
        free_cash_flow = info.get("freeCashflow")
        total_assets = _latest_statement_value(balance, "Total Assets")
        total_liabilities = _latest_statement_value(balance, "Total Liabilities Net Minority Interest")
        stockholders_equity = _latest_statement_value(balance, "Stockholders Equity")

        return "\n".join(
            [
                f"Financials for {ticker} ({name}):",
                f"Revenue: {_format(revenue, money=True)}",
                f"Revenue Growth: {_format(info.get('revenueGrowth'), percent=True)}",
                f"Net Income: {_format(net_income, money=True)}",
                f"Profit Margin: {_format(info.get('profitMargins'), percent=True)}",
                f"Operating Margin: {_format(info.get('operatingMargins'), percent=True)}",
                f"EBITDA: {_format(info.get('ebitda'), money=True)}",
                f"Earnings Growth: {_format(info.get('earningsGrowth'), percent=True)}",
                f"Operating Cash Flow: {_format(operating_cash_flow, money=True)}",
                f"Free Cash Flow: {_format(free_cash_flow, money=True)}",
                f"Total Assets: {_format(total_assets, money=True)}",
                f"Total Liabilities: {_format(total_liabilities, money=True)}",
                f"Stockholders' Equity: {_format(stockholders_equity, money=True)}",
                f"Debt/Equity: {_format(info.get('debtToEquity'))}",
                f"Return on Equity: {_format(info.get('returnOnEquity'), percent=True)}",
            ]
        )
    except Exception as exc:
        return f"Unable to fetch financial data for {ticker}: {exc}"


@function_tool
def get_earnings_transcript(symbol: str) -> str:
    """Fetch the latest earnings-call transcript for a company.

    Use this before preparing an earnings report. The returned transcript
    contains management commentary, financial highlights, guidance, risks,
    and analyst questions. The report should distinguish company statements
    from analysis and should not be presented as investment advice.

    Args:
        symbol: Stock ticker, such as AAPL, TSLA, or MSFT.
    """
    api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY", "").strip()
    if not api_key:
        return "FINANCIAL_MODELING_PREP_API_KEY is not set."

    ticker = symbol.strip().upper()
    if not ticker:
        return "Please provide a stock ticker symbol."

    params = urlencode({"symbol": ticker, "apikey": api_key})
    request = Request(
        f"https://financialmodelingprep.com/stable/earning-call-transcript?{params}",
        headers={"Accept": "application/json", "User-Agent": "ruby-finance-agent/1.0"},
    )

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=30, context=context) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 402:
            return (
                f"Financial Modeling Prep rejected the transcript request for {ticker} "
                "because this endpoint requires a plan with earnings-transcript access."
            )
        return f"Earnings transcript request failed for {ticker} (HTTP {exc.code})."
    except Exception as exc:
        return f"Unable to fetch earnings transcript for {ticker}: {exc}"

    if not isinstance(payload, list) or not payload:
        return f"No earnings transcript found for {ticker}."

    transcript = payload[0]
    content = (transcript.get("content") or transcript.get("transcript") or "").strip()
    if not content:
        return f"Earnings transcript for {ticker} did not contain transcript text."

    # Keep tool output within a practical model context size while preserving
    # the beginning, where management's prepared remarks usually start.
    if len(content) > 30_000:
        content = content[:29_997].rstrip() + "..."

    period = transcript.get("quarter") or "latest quarter"
    year = transcript.get("year")
    date = transcript.get("date") or "unknown date"
    return (
        f"Earnings transcript for {ticker} ({period} {year or ''}, {date}):\n\n"
        f"{content}"
    )
