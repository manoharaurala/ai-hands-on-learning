"""Company news retrieval with FMP as primary source and Yahoo fallback."""

from __future__ import annotations

import json
import logging
import os
import ssl
import threading
import time
from collections import OrderedDict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
import yfinance as yf
from agents import function_tool
from dotenv import load_dotenv

from .common import validate_ticker

FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_NEWS_PATH = "/news/stock"
REQUEST_TIMEOUT_SECONDS = 15
MAX_ARTICLES = 10
SUMMARY_MAX_CHARS = 320
CACHE_TTL_SECONDS = 300
CACHE_MAX_ENTRIES = 128
_POSITIVE_TERMS = {
    "beat",
    "beats",
    "growth",
    "grew",
    "gain",
    "gains",
    "upgrade",
    "upgraded",
    "profit",
    "record",
    "strong",
    "surge",
    "rise",
}
_NEGATIVE_TERMS = {
    "miss",
    "misses",
    "decline",
    "declined",
    "loss",
    "losses",
    "downgrade",
    "downgraded",
    "weak",
    "fall",
    "falls",
    "drop",
    "drops",
    "cut",
    "cuts",
}

_LOGGER = logging.getLogger(__name__)
_CACHE: OrderedDict[tuple[str, int], tuple[float, str]] = OrderedDict()
_CACHE_LOCK = threading.Lock()


def _validate_request(symbol: object, limit: object) -> tuple[str, int] | str:
    """Validate and normalize tool input before contacting a provider."""
    ticker, error = validate_ticker(symbol)
    if error:
        return error
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= MAX_ARTICLES
    ):
        return (
            f"The news limit must be an integer between 1 and {MAX_ARTICLES}."
        )
    return ticker, limit


def _safe_text(value: object, secret: str = "") -> str:
    """Normalize provider text and remove control characters and credentials."""
    text = " ".join(str(value or "").split())
    return text.replace(secret, "[redacted]") if secret else text


def _format_summary(value: object, secret: str = "") -> str:
    summary = _safe_text(value, secret)
    if not summary:
        return "No summary available."
    if len(summary) > SUMMARY_MAX_CHARS:
        return summary[: SUMMARY_MAX_CHARS - 1].rstrip() + "…"
    return summary


@function_tool
def analyze_sentiment(text: str) -> str:
    """Classify article wording with a small transparent term-based heuristic.

    Args:
        text: Headline or short article summary to classify.
    """
    if not isinstance(text, str) or not text.strip():
        return (
            "UNCLEAR: no text supplied. This is a lexical heuristic, "
            "not measured market sentiment."
        )
    words = set(
        "".join(
            char.lower() if char.isalpha() else " " for char in text
        ).split()
    )
    positive = len(words & _POSITIVE_TERMS)
    negative = len(words & _NEGATIVE_TERMS)
    if positive and negative:
        label = "MIXED"
    elif positive:
        label = "POSITIVE"
    elif negative:
        label = "NEGATIVE"
    else:
        label = "UNCLEAR"
    return (
        f"{label}: lexical counts positive={positive}, negative={negative}. "
        "This is a text heuristic, not measured investor or market sentiment."
    )


def _render_articles(
    ticker: str, source_label: str, articles: list[dict[str, str]]
) -> str:
    if not articles:
        return f"No recent financial news found for {ticker}."
    rendered = [
        f"{index}. {article['title']}\n"
        f"   Published: {article['published']}\n"
        f"   Publisher: {article['publisher']}\n"
        f"   Article URL: {article['url']}\n"
        f"   Summary: {article['summary']}"
        for index, article in enumerate(articles, start=1)
    ]
    return (
        f"Recent financial news for {ticker} ({source_label}):\n\n"
        + "\n\n".join(rendered)
    )


def _read_cache(ticker: str, limit: int) -> str | None:
    key = (ticker, limit)
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None
        created_at, value = entry
        if now - created_at >= CACHE_TTL_SECONDS:
            del _CACHE[key]
            return None
        _CACHE.move_to_end(key)
        return value


def _write_cache(ticker: str, limit: int, value: str) -> None:
    key = (ticker, limit)
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic(), value)
        _CACHE.move_to_end(key)
        while len(_CACHE) > CACHE_MAX_ENTRIES:
            _CACHE.popitem(last=False)


def _fmp_articles(
    payload: Any, limit: int, api_key: str
) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        return []
    articles: list[dict[str, str]] = []
    for article in payload:
        if not isinstance(article, dict):
            continue
        articles.append(
            {
                "title": _safe_text(
                    article.get("title")
                    or article.get("headline")
                    or "Untitled article",
                    api_key,
                ),
                "published": _safe_text(
                    article.get("publishedDate")
                    or article.get("published")
                    or "Unknown date/time",
                    api_key,
                ),
                "publisher": _safe_text(
                    article.get("publisher")
                    or article.get("site")
                    or "Unknown publisher",
                    api_key,
                ),
                "url": _safe_text(
                    article.get("url") or "No article URL available", api_key
                ),
                "summary": _format_summary(
                    article.get("text")
                    or article.get("content")
                    or article.get("summary"),
                    api_key,
                ),
            }
        )
        if len(articles) >= limit:
            break
    return articles


def _yahoo_articles(
    ticker: str, limit: int, secret: str = ""
) -> list[dict[str, str]]:
    """Retrieve and normalize Yahoo Finance's ticker news response."""
    payload = yf.Ticker(ticker).get_news(count=min(limit * 2, 20))
    articles: list[dict[str, str]] = []
    for item in payload or []:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, dict):
            continue

        finance = content.get("finance")
        symbol_items = (
            finance.get("stockTickers", []) if isinstance(finance, dict) else []
        )
        related_symbols = {
            str(value.get("symbol", "")).upper()
            for value in symbol_items
            if isinstance(value, dict)
        }
        # Treat articles without explicit ticker metadata as unverified. Yahoo's
        # broad news feed can otherwise return headlines for unrelated stocks.
        if ticker not in related_symbols:
            continue

        provider = content.get("provider")
        publisher = (
            provider.get("displayName")
            if isinstance(provider, dict)
            else provider
        )
        canonical_url = content.get("canonicalUrl")
        click_url = content.get("clickThroughUrl")
        article_url = (
            canonical_url.get("url")
            if isinstance(canonical_url, dict)
            else None
        )
        if not article_url and isinstance(click_url, dict):
            article_url = click_url.get("url")

        articles.append(
            {
                "title": _safe_text(
                    content.get("title") or "Untitled article", secret
                ),
                "published": _safe_text(
                    content.get("pubDate")
                    or content.get("displayTime")
                    or "Unknown date/time",
                    secret,
                ),
                "publisher": _safe_text(publisher or "Yahoo Finance", secret),
                "url": _safe_text(
                    article_url or "No article URL available", secret
                ),
                "summary": _format_summary(
                    content.get("summary") or content.get("description"), secret
                ),
            }
        )
        if len(articles) >= limit:
            break
    return articles


def _yahoo_fallback(
    ticker: str, limit: int, reason: str, secret: str = ""
) -> str:
    try:
        articles = _yahoo_articles(ticker, limit, secret)
    except Exception as exc:
        # Log only the exception type; provider errors can include request URLs.
        _LOGGER.warning("Yahoo news fallback failed (%s)", type(exc).__name__)
        return f"{reason} Yahoo Finance news is currently unavailable."
    if not articles:
        return (
            f"No recent financial news found for {ticker} from Yahoo Finance."
        )
    return _render_articles(ticker, "Yahoo Finance fallback", articles)


def _fallback_with_cache(
    ticker: str, limit: int, reason: str, secret: str = ""
) -> str:
    result = _yahoo_fallback(ticker, limit, reason, secret)
    if "currently unavailable" not in result:
        _write_cache(ticker, limit, result)
    return result


def _get_fmp_api_key() -> str:
    # Load local developer configuration lazily; existing process variables win.
    load_dotenv(override=False)
    return os.getenv("FINANCIAL_MODELING_PREP_API_KEY", "").strip()


def _fetch_fmp(ticker: str, limit: int, api_key: str) -> list[dict[str, str]]:
    query = urlencode({"symbols": ticker, "limit": limit})
    request = Request(
        f"{FMP_BASE_URL}{FMP_NEWS_PATH}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "ruby-finance-agent/1.0",
            # Header authentication keeps credentials out of request URLs.
            "apikey": api_key,
        },
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(
        request, timeout=REQUEST_TIMEOUT_SECONDS, context=ssl_context
    ) as response:
        payload = json.load(response)
    return _fmp_articles(payload, limit, api_key)


@function_tool
def get_financial_news(symbol: str, limit: int = 5) -> str:
    """Return recent company news from FMP, falling back to Yahoo Finance.

    Args:
        symbol: Stock ticker symbol, such as AAPL, TSLA, or TITAN.NS.
        limit: Maximum number of articles to return, from 1 to 10.
    """
    validated = _validate_request(symbol, limit)
    if isinstance(validated, str):
        return validated
    ticker, article_limit = validated

    cached = _read_cache(ticker, article_limit)
    if cached is not None:
        return cached

    api_key = _get_fmp_api_key()
    if not api_key:
        return _fallback_with_cache(
            ticker,
            article_limit,
            "Financial Modeling Prep is not configured. ",
        )

    try:
        articles = _fetch_fmp(ticker, article_limit, api_key)
    except HTTPError as exc:
        status = exc.code
        exc.close()
        if status in (400, 401, 402, 403, 404, 429) or status >= 500:
            _LOGGER.info(
                "FMP news request returned HTTP %s; trying Yahoo Finance",
                status,
            )
            return _fallback_with_cache(
                ticker,
                article_limit,
                "Financial Modeling Prep news is unavailable "
                f"(HTTP {status}). ",
                api_key,
            )
        return f"Financial news request failed (HTTP {status})."
    except (URLError, TimeoutError, ssl.SSLError, OSError) as exc:
        _LOGGER.info(
            "FMP news request failed (%s); trying Yahoo Finance",
            type(exc).__name__,
        )
        return _fallback_with_cache(
            ticker,
            article_limit,
            "Financial Modeling Prep could not be reached. ",
            api_key,
        )
    except json.JSONDecodeError, UnicodeDecodeError:
        _LOGGER.warning(
            "FMP returned an unreadable news response; trying Yahoo Finance"
        )
        return _fallback_with_cache(
            ticker,
            article_limit,
            "Financial Modeling Prep returned unreadable data. ",
            api_key,
        )
    except Exception as exc:
        # Do not log exception text: HTTP libraries may include request details.
        _LOGGER.warning(
            "FMP news request failed unexpectedly (%s)", type(exc).__name__
        )
        return _fallback_with_cache(
            ticker,
            article_limit,
            "Financial Modeling Prep news is unavailable. ",
            api_key,
        )

    if not articles:
        return _fallback_with_cache(ticker, article_limit, "", api_key)

    result = _render_articles(ticker, "Financial Modeling Prep", articles)
    _write_cache(ticker, article_limit, result)
    return result
