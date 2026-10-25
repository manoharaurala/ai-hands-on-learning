"""Yahoo Finance tools for the finance agent."""

import math

import yfinance as yf
from agents import function_tool


def _format_number(value: object, *, money: bool = False, percent: bool = False) -> str:
    """Format Yahoo Finance values while handling missing or invalid data."""
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


@function_tool
def get_company_valuation(symbol: str) -> str:
    """Get current valuation metrics for a public company from Yahoo Finance.

    Use this tool when the user asks about a company's valuation, multiples,
    market capitalization, or profitability metrics. The symbol should be a
    Yahoo Finance ticker, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker = symbol.strip().upper()
    if not ticker:
        return "Please provide a stock ticker symbol."

    try:
        info = yf.Ticker(ticker).info
        if not info:
            return f"No valuation data found for {ticker}."

        price = info.get("currentPrice")
        if price is None:
            price = info.get("regularMarketPrice")

        company_name = info.get("longName") or info.get("shortName") or ticker
        return "\n".join(
            [
                f"Valuation for {ticker} ({company_name}):",
                f"Price: {_format_number(price, money=True)}",
                f"Market Cap: {_format_number(info.get('marketCap'), money=True)}",
                f"Trailing P/E: {_format_number(info.get('trailingPE'))}",
                f"Forward P/E: {_format_number(info.get('forwardPE'))}",
                f"Price/Sales: {_format_number(info.get('priceToSalesTrailing12Months'))}",
                f"Price/Book: {_format_number(info.get('priceToBook'))}",
                f"Enterprise Value: {_format_number(info.get('enterpriseValue'), money=True)}",
                f"EV/EBITDA: {_format_number(info.get('enterpriseToEbitda'))}",
                f"Revenue Growth: {_format_number(info.get('revenueGrowth'), percent=True)}",
                f"Profit Margin: {_format_number(info.get('profitMargins'), percent=True)}",
            ]
        )
    except Exception as exc:
        return f"Unable to fetch valuation data for {ticker}: {exc}"