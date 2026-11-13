"""Yahoo Finance valuation tools: market multiples, peer comparison, and DCF."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import median
from typing import Any
from urllib.parse import quote

import pandas as pd
import yfinance as yf
from agents import function_tool

from .common import (
    YAHOO_INFO_CACHE,
    YAHOO_STATEMENT_CACHE,
    normalize_label,
    validate_ticker,
)

_MAX_PEERS = 8
_DCF_METRICS = (
    ("Trailing P/E", "trailingPE"),
    ("Forward P/E", "forwardPE"),
    ("EV/EBITDA", "enterpriseToEbitda"),
    ("Price/Sales", "priceToSalesTrailing12Months"),
    ("Price/Book", "priceToBook"),
)


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except TypeError, ValueError:
        pass
    try:
        result = float(value)
    except TypeError, ValueError, OverflowError:
        return None
    return result if math.isfinite(result) else None


def _format_number(value: object, *, percent: bool = False) -> str:
    number = _number(value)
    if number is None:
        return "N/A"
    if percent:
        return f"{number * 100:.2f}%"
    return f"{number:,.2f}"


def _format_money(value: float | None, currency: str) -> str:
    if value is None:
        return "N/A"
    return (
        f"{currency} {value:,.2f}"
        if currency != "N/A"
        else f"{value:,.2f} (currency N/A)"
    )


def _discounted_equity_cash_flows(
    base_fcf: float,
    forecast_years: int,
    growth_rate: float,
    cost_of_equity: float,
    terminal_growth_rate: float,
) -> tuple[float, float, float]:
    """Return forecast PV, terminal PV, and their equity-value sum."""
    projected_fcfs = [
        base_fcf * (1 + growth_rate) ** year
        for year in range(1, forecast_years + 1)
    ]
    forecast_pv = sum(
        cash_flow / (1 + cost_of_equity) ** year
        for year, cash_flow in enumerate(projected_fcfs, start=1)
    )
    terminal_value = (
        projected_fcfs[-1]
        * (1 + terminal_growth_rate)
        / (cost_of_equity - terminal_growth_rate)
    )
    terminal_pv = terminal_value / (1 + cost_of_equity) ** forecast_years
    return forecast_pv, terminal_pv, forecast_pv + terminal_pv


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _quote_as_of(info: dict[str, Any]) -> str:
    timestamp = _number(info.get("regularMarketTime"))
    if timestamp is None:
        return "N/A"
    try:
        return datetime.fromtimestamp(timestamp, timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    except OverflowError, OSError, ValueError:
        return "N/A"


def _latest_period(frame: object) -> object | None:
    if (
        not isinstance(frame, pd.DataFrame)
        or frame.empty
        or len(frame.columns) == 0
    ):
        return None
    try:
        return max(frame.columns, key=lambda value: pd.Timestamp(value).value)
    except TypeError, ValueError, OverflowError:
        return frame.columns[0]


def _statement_value(
    frame: object, aliases: tuple[str, ...]
) -> tuple[float | None, str]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None, "N/A"
    rows = {normalize_label(label): label for label in frame.index}
    row = next(
        (
            rows[normalize_label(alias)]
            for alias in aliases
            if normalize_label(alias) in rows
        ),
        None,
    )
    period = _latest_period(frame)
    if row is None or period is None:
        return None, "N/A"
    try:
        value = _number(frame.at[row, period])
    except KeyError, TypeError, ValueError:
        return None, "N/A"
    try:
        period_label = pd.Timestamp(period).strftime("%Y-%m-%d")
    except TypeError, ValueError, OverflowError:
        period_label = str(period)
    return value, period_label


def _get_info(ticker: str) -> dict[str, Any]:
    def load() -> dict[str, Any]:
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            return {}
        return info if isinstance(info, dict) else {}

    return YAHOO_INFO_CACHE.get_or_load(ticker, load)


def _get_price(info: dict[str, Any]) -> float | None:
    return _number(info.get("currentPrice")) or _number(
        info.get("regularMarketPrice")
    )


def _get_financial_currency(info: dict[str, Any]) -> str:
    value = info.get("financialCurrency")
    return str(value).strip().upper() if value else "N/A"


def _get_quote_currency(info: dict[str, Any]) -> str:
    value = info.get("currency")
    return str(value).strip().upper() if value else "N/A"


@function_tool
def get_company_valuation(symbol: str) -> str:
    """Get current price and common valuation multiples for a public company.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    try:
        info = _get_info(ticker)
        if not info:
            return f"No valuation data found for {ticker}."
        price = _get_price(info)
        company_name = info.get("longName") or info.get("shortName") or ticker
        currency = _get_quote_currency(info)
        lines = [
            f"Valuation for {ticker} ({company_name})",
            f"Quote as of: {_quote_as_of(info)} | Retrieved: {_now_utc()} | "
            f"Currency: {currency}",
            f"Price: {_format_money(price, currency)}",
            "Market Cap: "
            f"{_format_money(_number(info.get('marketCap')), currency)}",
            f"Trailing P/E: {_format_number(info.get('trailingPE'))}",
            f"Forward P/E: {_format_number(info.get('forwardPE'))}",
            "Price/Sales: "
            f"{_format_number(info.get('priceToSalesTrailing12Months'))}",
            f"Price/Book: {_format_number(info.get('priceToBook'))}",
            "Enterprise Value: "
            f"{_format_money(_number(info.get('enterpriseValue')), currency)}",
            f"EV/EBITDA: {_format_number(info.get('enterpriseToEbitda'))}",
            "Revenue Growth: "
            f"{_format_number(info.get('revenueGrowth'), percent=True)}",
            "Profit Margin: "
            f"{_format_number(info.get('profitMargins'), percent=True)}",
            "Source: https://finance.yahoo.com/quote/"
            f"{quote(ticker, safe='')}/",
        ]
        return "\n".join(lines)
    except Exception:
        return f"Unable to fetch valuation data for {ticker} right now."


@function_tool
def run_dcf_model(
    symbol: str,
    forecast_years: int = 5,
    fcf_growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.025,
) -> str:
    """Run an illustrative equity cash-flow DCF using explicit assumptions.

    Reported free cash flow is treated as an FCFE-like proxy and discounted
    directly to equity. The discount rate is therefore an assumed cost of
    equity; the model does not apply an enterprise-value debt/cash bridge.
    Rates are decimal annual rates (0.05 means 5%). Projections are scenarios,
    not forecasts or reliable intrinsic-value estimates.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL or MSFT.
        forecast_years: Number of explicit forecast years, from 1 through 10.
        fcf_growth_rate: Assumed annual free-cash-flow growth from -99% to 100%.
        discount_rate: Assumed cost of equity, above terminal growth and at
            most 100%.
        terminal_growth_rate: Assumed perpetual growth from -10% to below the
            discount rate.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    if (
        isinstance(forecast_years, bool)
        or not isinstance(forecast_years, int)
        or not 1 <= forecast_years <= 10
    ):
        return "Forecast years must be an integer between 1 and 10."
    growth = _number(fcf_growth_rate)
    discount = _number(discount_rate)
    terminal_growth = _number(terminal_growth_rate)
    if growth is None or not -0.99 <= growth <= 1.0:
        return "FCF growth assumption must be between -99% and 100%."
    if discount is None or not 0 < discount <= 1.0:
        return "Discount rate must be greater than 0% and no more than 100%."
    if terminal_growth is None or not -0.10 <= terminal_growth < discount:
        return "Terminal growth must be between -10% and the discount rate."

    as_of = _now_utc()
    assumptions = (
        "Scenario assumptions (not forecasts): "
        f"horizon={forecast_years} years; "
        f"annual FCF growth={growth:.2%}; "
        f"assumed cost of equity={discount:.2%}; "
        f"terminal growth={terminal_growth:.2%}."
    )
    try:
        instrument = yf.Ticker(ticker)
        cash_flow = YAHOO_STATEMENT_CACHE.get_or_load(
            (ticker, "cash_flow"), lambda: instrument.cash_flow
        )
        info = _get_info(ticker)
    except Exception:
        return (
            f"DCF unavailable for {ticker}: Yahoo Finance could not retrieve "
            f"the required financial data.\n{assumptions}"
        )

    base_fcf, fcf_period = _statement_value(cash_flow, ("Free Cash Flow",))
    fcf_basis = "reported free cash flow"
    if base_fcf is None:
        operating_cash_flow, _ = _statement_value(
            cash_flow,
            (
                "Operating Cash Flow",
                "Cash Flow From Continuing Operating Activities",
            ),
        )
        capex, _ = _statement_value(cash_flow, ("Capital Expenditure",))
        if operating_cash_flow is not None and capex is not None:
            base_fcf = operating_cash_flow - abs(capex)
            fcf_basis = "operating cash flow less absolute capital expenditure"
            fcf_period = _statement_value(
                cash_flow,
                (
                    "Operating Cash Flow",
                    "Cash Flow From Continuing Operating Activities",
                ),
            )[1]

    currency = _get_financial_currency(info)
    report = [
        f"Illustrative equity cash-flow DCF scenario for {ticker}",
        f"Retrieved: {as_of} UTC | Statement currency: {currency}",
        assumptions,
        f"Base FCF ({fcf_period}; {fcf_basis}): "
        f"{_format_money(base_fcf, currency)}",
    ]
    if base_fcf is None:
        report.append(
            "Scenario value per share: N/A (free cash flow is missing)."
        )
        return "\n".join(report)
    if base_fcf <= 0:
        report.append(
            "Scenario value per share is N/A: terminal value requires positive "
            "base free cash flow."
        )
        return "\n".join(report)

    pv_forecast, pv_terminal_value, equity_value_scenario = (
        _discounted_equity_cash_flows(
            base_fcf,
            forecast_years,
            growth,
            discount,
            terminal_growth,
        )
    )
    shares = _number(info.get("sharesOutstanding"))
    value_per_share = (
        equity_value_scenario / shares
        if shares is not None and shares > 0
        else None
    )
    price = _get_price(info)
    quote_currency = _get_quote_currency(info)
    same_currency = currency != "N/A" and currency == quote_currency
    upside = (
        value_per_share / price - 1
        if value_per_share is not None
        and price is not None
        and price > 0
        and same_currency
        else None
    )

    report.extend(
        [
            "Present value of forecast FCF: "
            f"{_format_money(pv_forecast, currency)}",
            "Present value of terminal value: "
            f"{_format_money(pv_terminal_value, currency)}",
            "Illustrative equity cash-flow value: "
            f"{_format_money(equity_value_scenario, currency)}",
            f"Shares outstanding: {_format_number(shares)}",
            "Scenario value per share (not intrinsic value): "
            f"{_format_money(value_per_share, currency)}",
            "Current share price: "
            f"{_format_money(price, quote_currency)} "
            f"(quote as of {_quote_as_of(info)})",
            (
                "Implied upside/downside: "
                f"{_format_number(upside, percent=True)}"
                if same_currency
                else "Implied upside/downside: N/A (statement and quote "
                "currencies are missing or differ)."
            ),
            "Method: reported FCF is treated as an FCFE-like proxy and "
            "discounted at the assumed cost of equity; no cash/debt bridge.",
            "This simplified educational scenario is not a reliable "
            "intrinsic-value estimate or investment advice.",
            "Source: https://finance.yahoo.com/quote/"
            f"{quote(ticker, safe='')}/financials/",
        ]
    )
    return "\n".join(report)


def _parse_peer_symbols(
    peer_symbols: object, target: str
) -> tuple[list[str] | None, str | None]:
    if not isinstance(peer_symbols, str) or not peer_symbols.strip():
        return (
            None,
            "Provide explicit peer tickers as a comma-separated list; "
            "peer companies are not guessed.",
        )
    peers: list[str] = []
    for raw in peer_symbols.split(","):
        candidate, error = validate_ticker(raw)
        if error:
            return None, f"Invalid peer ticker: {raw.strip() or '(empty)'}."
        if candidate == target:
            continue
        if candidate not in peers:
            peers.append(candidate)
    if not peers:
        return (
            None,
            "Provide at least one peer ticker other than the target company.",
        )
    if len(peers) > _MAX_PEERS:
        return None, f"Provide no more than {_MAX_PEERS} peer tickers."
    return peers, None


def _peer_info(ticker: str) -> dict[str, Any]:
    return _get_info(ticker)


def _peer_multiple_text(value: object) -> str:
    number = _number(value)
    if number is None:
        return "N/A"
    if number <= 0:
        return f"N/M ({number:,.2f}; non-positive)"
    return _format_number(number)


@function_tool
def get_peer_multiples(symbol: str, peer_symbols: str) -> str:
    """Compare valuation multiples for a company and explicitly named peers.

    Only the supplied peer tickers are used; the tool never invents comparable
    companies. Multiples are sourced from Yahoo Finance's company quote data.

    Args:
        symbol: Target Yahoo Finance ticker symbol.
        peer_symbols: Explicit comma-separated peer tickers, for example
            MSFT,GOOGL.
    """
    target, error = validate_ticker(symbol)
    if error:
        return error
    peers, error = _parse_peer_symbols(peer_symbols, target)
    if error:
        return error

    tickers = [target, *peers]
    retrieved = _now_utc()
    info_by_ticker = {ticker: _peer_info(ticker) for ticker in tickers}
    rows: list[str] = []

    for ticker in tickers:
        info = info_by_ticker[ticker]
        company = str(info.get("longName") or info.get("shortName") or ticker)
        currency = _get_quote_currency(info)
        values = [_peer_multiple_text(info.get(key)) for _, key in _DCF_METRICS]
        rows.append(
            f"{ticker} ({company}; {currency}; "
            f"quote as of {_quote_as_of(info)}) | "
            + " | ".join(values)
            + f" | https://finance.yahoo.com/quote/{quote(ticker, safe='')}/"
        )

    median_values = []
    # Exclude the target company from peer medians.
    for label, key in _DCF_METRICS:
        values = [_number(info_by_ticker[ticker].get(key)) for ticker in peers]
        valid = [value for value in values if value is not None and value > 0]
        median_values.append(
            _format_number(median(valid))
            if valid
            else "N/A (no meaningful peer values)"
        )

    header = (
        "Ticker (company; quote currency; quote as of) | "
        + " | ".join(label for label, _ in _DCF_METRICS)
        + " | Yahoo Finance source"
    )
    median_row = "Peer median (provided peers) | " + " | ".join(median_values)
    return (
        f"Peer valuation multiples | Retrieved: {retrieved} UTC\n"
        "Multiples are provider-reported. Non-positive values are marked N/M "
        "and excluded from medians; missing values are also excluded. "
        "Peers were supplied explicitly.\n"
        + header
        + "\n"
        + "\n".join(rows)
        + "\n"
        + median_row
    )
