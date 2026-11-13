"""Yahoo Finance tools for company statements and basic financial ratios."""

from __future__ import annotations

import math
from urllib.parse import quote

import pandas as pd
import yfinance as yf
from agents import function_tool

from .common import (
    YAHOO_STATEMENT_CACHE,
    normalize_label,
    validate_ticker,
)

_MAX_PERIODS = 4
_MAX_ROWS = 24

_INCOME_ROWS = (
    "Total Revenue",
    "Operating Revenue",
    "Cost Of Revenue",
    "Gross Profit",
    "Operating Expense",
    "Operating Income",
    "Interest Expense",
    "Pretax Income",
    "Tax Provision",
    "Net Income",
    "Basic EPS",
    "Diluted EPS",
    "Basic Average Shares",
    "Diluted Average Shares",
)
_BALANCE_ROWS = (
    "Cash And Cash Equivalents",
    "Cash Cash Equivalents And Short Term Investments",
    "Current Assets",
    "Total Assets",
    "Current Liabilities",
    "Long Term Debt",
    "Total Debt",
    "Total Liabilities Net Minority Interest",
    "Stockholders Equity",
    "Working Capital",
    "Net Tangible Assets",
)
_CASH_FLOW_ROWS = (
    "Operating Cash Flow",
    "Cash Flow From Continuing Operating Activities",
    "Capital Expenditure",
    "Free Cash Flow",
    "Investing Cash Flow",
    "Financing Cash Flow",
    "Net Income From Continuing Operations",
    "Depreciation And Amortization",
    "Stock Based Compensation",
    "Repayment Of Debt",
    "Issuance Of Debt",
)


def _period_sort_key(period: object) -> int:
    try:
        return int(pd.Timestamp(period).timestamp())
    except TypeError, ValueError, OverflowError:
        return 0


def _period_label(period: object) -> str:
    try:
        return pd.Timestamp(period).strftime("%Y-%m-%d")
    except TypeError, ValueError, OverflowError:
        return str(period)


def _format_value(value: object) -> str:
    if value is None:
        return "N/A"
    try:
        if bool(pd.isna(value)):
            return "N/A"
    except TypeError, ValueError:
        pass
    try:
        number = float(value)
    except TypeError, ValueError:
        return str(value)
    if not math.isfinite(number):
        return "N/A"
    if number.is_integer():
        return f"{number:,.0f}"
    return f"{number:,.2f}"


def _ordered_periods(frame: pd.DataFrame) -> list[object]:
    return sorted(frame.columns, key=_period_sort_key, reverse=True)[
        :_MAX_PERIODS
    ]


def _matching_rows(
    frame: pd.DataFrame, preferred: tuple[str, ...]
) -> list[object]:
    labels = {normalize_label(label): label for label in frame.index}
    selected: list[object] = []
    for wanted in preferred:
        label = labels.get(normalize_label(wanted))
        if label is not None and label not in selected:
            selected.append(label)
    if selected:
        return selected
    return list(frame.index[:_MAX_ROWS])


def _format_statement(
    ticker: str,
    title: str,
    frame: object,
    preferred_rows: tuple[str, ...],
) -> str:
    if (
        not isinstance(frame, pd.DataFrame)
        or frame.empty
        or len(frame.columns) == 0
    ):
        return f"No {title.lower()} data found for {ticker}."

    periods = _ordered_periods(frame)
    if not periods:
        return f"No {title.lower()} data found for {ticker}."
    rows = _matching_rows(frame, preferred_rows)
    if not rows:
        return f"No {title.lower()} data found for {ticker}."

    header = "Metric | " + " | ".join(
        _period_label(period) for period in periods
    )
    lines = [header]
    for row in rows:
        values = [_format_value(frame.at[row, period]) for period in periods]
        if all(value == "N/A" for value in values):
            continue
        lines.append(f"{row} | " + " | ".join(values))
        if len(lines) - 1 >= _MAX_ROWS:
            break
    if len(lines) == 1:
        return f"No {title.lower()} data found for {ticker}."
    return "\n".join(
        [
            f"{title} for {ticker} (Yahoo Finance annual periods; "
            "statement response does not include a currency/unit label):",
            *lines,
            f"Source: https://finance.yahoo.com/quote/"
            f"{quote(ticker, safe='')}/{_statement_page(title)}",
        ]
    )


def _statement_page(title: str) -> str:
    if title == "Income statement":
        return "financials/"
    if title == "Balance sheet":
        return "balance-sheet/"
    return "cash-flow/"


def _fetch_statement(ticker: str, attribute: str) -> pd.DataFrame:
    def load() -> pd.DataFrame:
        statement = getattr(yf.Ticker(ticker), attribute)
        return (
            statement if isinstance(statement, pd.DataFrame) else pd.DataFrame()
        )

    return YAHOO_STATEMENT_CACHE.get_or_load((ticker, attribute), load)


@function_tool
def get_income_statement(symbol: str) -> str:
    """Get up to four annual income-statement periods for a public company.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    try:
        frame = _fetch_statement(ticker, "income_stmt")
        return _format_statement(
            ticker, "Income statement", frame, _INCOME_ROWS
        )
    except Exception:
        return (
            f"Unable to retrieve the income statement for {ticker} right now."
        )


@function_tool
def get_balance_sheet(symbol: str) -> str:
    """Get up to four annual balance-sheet periods for a public company.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    try:
        frame = _fetch_statement(ticker, "balance_sheet")
        return _format_statement(ticker, "Balance sheet", frame, _BALANCE_ROWS)
    except Exception:
        return f"Unable to retrieve the balance sheet for {ticker} right now."


@function_tool
def get_cash_flow_statement(symbol: str) -> str:
    """Get up to four annual cash-flow-statement periods for a public company.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    try:
        frame = _fetch_statement(ticker, "cash_flow")
        return _format_statement(
            ticker, "Cash flow statement", frame, _CASH_FLOW_ROWS
        )
    except Exception:
        return (
            f"Unable to retrieve the cash flow statement for {ticker} "
            "right now."
        )


def _period_key(period: object) -> str | None:
    try:
        return pd.Timestamp(period).date().isoformat()
    except TypeError, ValueError, OverflowError:
        return None


def _value_for_period(
    frame: pd.DataFrame, aliases: tuple[str, ...], period: object
) -> float | None:
    if frame.empty:
        return None
    target_key = _period_key(period)
    if target_key is None:
        return None
    column = next(
        (
            column
            for column in frame.columns
            if _period_key(column) == target_key
        ),
        None,
    )
    if column is None:
        return None
    rows = {normalize_label(label): label for label in frame.index}
    row = next(
        (
            rows.get(normalize_label(alias))
            for alias in aliases
            if rows.get(normalize_label(alias)) is not None
        ),
        None,
    )
    if row is None:
        return None
    try:
        number = float(frame.at[row, column])
    except TypeError, ValueError, OverflowError:
        return None
    return number if math.isfinite(number) else None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    result = numerator / denominator
    return result if math.isfinite(result) else None


def _average_assets_roa(
    net_income: float | None, balance: pd.DataFrame, income_period: object
) -> float | None:
    current_assets = _value_for_period(
        balance, ("Total Assets",), income_period
    )
    income_key = _period_key(income_period)
    prior_period = next(
        (
            period
            for period in _ordered_periods(balance)
            if _period_key(period) != income_key
            and _period_sort_key(period) < _period_sort_key(income_period)
        ),
        None,
    )
    prior_assets = (
        _value_for_period(balance, ("Total Assets",), prior_period)
        if prior_period is not None
        else None
    )
    if current_assets is None or prior_assets is None:
        return None
    return _ratio(net_income, (current_assets + prior_assets) / 2)


def _display_ratio(value: float | None, *, percent: bool = False) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%" if percent else f"{value:.2f}x"


@function_tool
def compute_key_ratios(symbol: str) -> str:
    """Compute ratios from annual statements; missing inputs are N/A.

    Args:
        symbol: Yahoo Finance ticker symbol, such as AAPL, TSLA, or TITAN.NS.
    """
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    try:
        instrument = yf.Ticker(ticker)
        income = instrument.income_stmt
        balance = instrument.balance_sheet
        cash_flow = instrument.cash_flow
        income = income if isinstance(income, pd.DataFrame) else pd.DataFrame()
        balance = (
            balance if isinstance(balance, pd.DataFrame) else pd.DataFrame()
        )
        cash_flow = (
            cash_flow if isinstance(cash_flow, pd.DataFrame) else pd.DataFrame()
        )

        income_periods = _ordered_periods(income)
        balance_periods = _ordered_periods(balance)
        cash_flow_periods = _ordered_periods(cash_flow)
        income_period = income_periods[0] if income_periods else None
        balance_period = balance_periods[0] if balance_periods else None

        revenue = (
            _value_for_period(
                income, ("Total Revenue", "Operating Revenue"), income_period
            )
            if income_period is not None
            else None
        )
        net_income = (
            _value_for_period(
                income,
                ("Net Income", "Net Income Common Stockholders"),
                income_period,
            )
            if income_period is not None
            else None
        )
        current_assets = (
            _value_for_period(balance, ("Current Assets",), balance_period)
            if balance_period is not None
            else None
        )
        current_liabilities = (
            _value_for_period(balance, ("Current Liabilities",), balance_period)
            if balance_period is not None
            else None
        )
        debt = (
            _value_for_period(balance, ("Total Debt",), balance_period)
            if balance_period is not None
            else None
        )
        if debt is None:
            short_term_debt = (
                _value_for_period(
                    balance,
                    ("Current Debt", "Short Long Term Debt"),
                    balance_period,
                )
                if balance_period is not None
                else None
            )
            long_term_debt = (
                _value_for_period(
                    balance,
                    (
                        "Long Term Debt",
                        "Long Term Debt And Capital Lease Obligation",
                    ),
                    balance_period,
                )
                if balance_period is not None
                else None
            )
            if short_term_debt is not None and long_term_debt is not None:
                debt = short_term_debt + long_term_debt
        equity = (
            _value_for_period(
                balance,
                ("Stockholders Equity", "Total Stockholder Equity"),
                balance_period,
            )
            if balance_period is not None
            else None
        )
        cash = (
            _value_for_period(
                balance,
                (
                    "Cash Cash Equivalents And Short Term Investments",
                    "Cash And Cash Equivalents",
                ),
                balance_period,
            )
            if balance_period is not None
            else None
        )
        cash_period = next(
            (
                period
                for period in cash_flow_periods
                if _period_key(period) == _period_key(income_period)
            ),
            None,
        )
        operating_cash_flow = (
            _value_for_period(
                cash_flow,
                (
                    "Operating Cash Flow",
                    "Cash Flow From Continuing Operating Activities",
                ),
                cash_period,
            )
            if cash_period is not None
            else None
        )
        free_cash_flow = (
            _value_for_period(cash_flow, ("Free Cash Flow",), cash_period)
            if cash_period is not None
            else None
        )
        if free_cash_flow is None:
            capex = (
                _value_for_period(
                    cash_flow, ("Capital Expenditure",), cash_period
                )
                if cash_period is not None
                else None
            )
            if operating_cash_flow is not None and capex is not None:
                free_cash_flow = operating_cash_flow - abs(capex)

        roa = (
            _average_assets_roa(net_income, balance, income_period)
            if income_period is not None
            else None
        )

        results = [
            (
                "Current ratio",
                _display_ratio(_ratio(current_assets, current_liabilities)),
            ),
            ("Cash ratio", _display_ratio(_ratio(cash, current_liabilities))),
            ("Debt-to-equity", _display_ratio(_ratio(debt, equity))),
            (
                "Net margin",
                _display_ratio(_ratio(net_income, revenue), percent=True),
            ),
            (
                "Return on assets (average assets)",
                _display_ratio(roa, percent=True),
            ),
            (
                "Operating cash-flow margin",
                _display_ratio(
                    _ratio(operating_cash_flow, revenue), percent=True
                ),
            ),
            (
                "Free cash-flow margin",
                _display_ratio(_ratio(free_cash_flow, revenue), percent=True),
            ),
        ]
        income_label = (
            _period_label(income_period) if income_period is not None else "N/A"
        )
        balance_label = (
            _period_label(balance_period)
            if balance_period is not None
            else "N/A"
        )
        cash_label = (
            _period_label(cash_period) if cash_period is not None else "N/A"
        )
        output_lines = [
            f"Key ratios for {ticker} "
            "(calculated from annual statement values):",
            f"Income period: {income_label}",
            f"Balance-sheet period: {balance_label}",
            f"Cash-flow period aligned to income statement: {cash_label}",
            *(f"{name}: {value}" for name, value in results),
            "Source: Yahoo Finance annual financials "
            f"https://finance.yahoo.com/quote/{quote(ticker, safe='')}"
            "/financials/",
        ]
        return "\n".join(output_lines)
    except Exception:
        return (
            f"Unable to compute key ratios for {ticker} because financial "
            "statements could not be retrieved."
        )
