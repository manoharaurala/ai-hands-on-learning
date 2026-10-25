"""Financial news tools backed by Financial Modeling Prep."""

import json
import os
import ssl
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import certifi
from agents import function_tool

FMP_BASE_URL = "https://financialmodelingprep.com/stable"


@function_tool
def get_financial_news(symbol: str, limit: int = 5) -> str:
    """Get recent company news from Financial Modeling Prep.

    Args:
        symbol: Stock ticker symbol, such as AAPL, TSLA, or TITAN.NS.
        limit: Maximum number of articles to return, from 1 to 10.
    """
    api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY", "").strip()
    if not api_key:
        return "FINANCIAL_MODELING_PREP_API_KEY is not set."

    ticker = symbol.strip().upper()
    if not ticker:
        return "Please provide a stock ticker symbol."

    try:
        article_limit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        return "The news limit must be an integer between 1 and 10."

    params = urlencode({"symbols": ticker, "limit": article_limit, "apikey": api_key})
    request = Request(
        f"{FMP_BASE_URL}/news/stock-latest?{params}",
        headers={"Accept": "application/json", "User-Agent": "ruby-finance-agent/1.0"},
    )

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=20, context=ssl_context) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 402:
            return (
                f"Financial Modeling Prep rejected the news request for {ticker} "
                "because this endpoint requires a plan with news access."
            )
        return f"Financial news request failed for {ticker} (HTTP {exc.code})."
    except Exception as exc:
        return f"Unable to fetch financial news for {ticker}: {exc}"

    if not isinstance(payload, list) or not payload:
        return f"No recent financial news found for {ticker}."

    articles = []
    for article in payload[:article_limit]:
        title = article.get("title") or "Untitled article"
        published = article.get("publishedDate") or article.get("published") or "Unknown date"
        source = article.get("site") or article.get("publisher") or "Unknown source"
        url = article.get("url") or "No link"
        summary = (article.get("text") or article.get("content") or "").strip()
        if len(summary) > 400:
            summary = summary[:397].rstrip() + "..."
        articles.append(
            f"{len(articles) + 1}. {title}\n"
            f"   Date: {published} | Source: {source}\n"
            f"   Summary: {summary or 'No summary available.'}\n"
            f"   Link: {url}"
        )

    return f"Recent financial news for {ticker}:\n\n" + "\n\n".join(articles)
