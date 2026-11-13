"""Common validation and normalization for finance provider tools."""

from __future__ import annotations

import re
import copy
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Hashable
from typing import TypeVar

_TICKER_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.\-^=]{0,19}$")
_Value = TypeVar("_Value")


class TTLCache:  # pylint: disable=too-few-public-methods
    """Small bounded cache that coalesces concurrent provider requests."""

    def __init__(self, ttl_seconds: float, max_entries: int = 128) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._values: OrderedDict[Hashable, tuple[float, object]] = (
            OrderedDict()
        )
        self._condition = threading.Condition()
        self._loading: set[Hashable] = set()

    def get_or_load(
        self, key: Hashable, loader: Callable[[], _Value]
    ) -> _Value:
        """Return a copy of a fresh cached value or load it once."""
        with self._condition:
            while True:
                entry = self._values.get(key)
                if entry is not None:
                    created, value = entry
                    if time.monotonic() - created < self._ttl_seconds:
                        self._values.move_to_end(key)
                        return copy.deepcopy(value)  # type: ignore[return-value]
                    del self._values[key]
                if key not in self._loading:
                    self._loading.add(key)
                    break
                self._condition.wait()

        try:
            value = loader()
            cached_value = copy.deepcopy(value)
        except BaseException:
            with self._condition:
                self._loading.discard(key)
                self._condition.notify_all()
            raise

        with self._condition:
            self._values[key] = (time.monotonic(), cached_value)
            self._values.move_to_end(key)
            while len(self._values) > self._max_entries:
                self._values.popitem(last=False)
            self._loading.discard(key)
            self._condition.notify_all()
        return value


YAHOO_STATEMENT_CACHE = TTLCache(ttl_seconds=300)
YAHOO_INFO_CACHE = TTLCache(ttl_seconds=60)


def validate_ticker(symbol: object) -> tuple[str | None, str | None]:
    """Return a normalized ticker or a safe validation error."""
    if not isinstance(symbol, str):
        return None, "Please provide a valid stock ticker symbol."
    ticker = symbol.strip().upper()
    if (
        not ticker
        or not _TICKER_PATTERN.fullmatch(ticker)
        or ".." in ticker
        or "--" in ticker
        or ticker.endswith((".", "-", "="))
    ):
        return (
            None,
            "Please provide a valid stock ticker symbol "
            "(for example, AAPL or BRK.B).",
        )
    return ticker, None


def normalize_label(value: object) -> str:
    """Normalize provider statement labels for alias comparisons."""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())
