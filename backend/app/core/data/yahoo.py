"""Yahoo Finance quotes for watchlist price cards."""

from __future__ import annotations

import concurrent.futures as cf
import logging
import time
from dataclasses import dataclass
from typing import Optional

import yfinance as yf

log = logging.getLogger(__name__)

_CACHE: dict[tuple[str, ...], tuple[float, dict[str, "YahooQuote"]]] = {}
_CACHE_TTL = 15.0


@dataclass
class YahooQuote:
    symbol: str
    price: float
    rth_price: float
    prev_close: float
    market_state: str
    bid: Optional[float]
    ask: Optional[float]

    @property
    def change_pct(self) -> float:
        if self.prev_close == 0:
            return 0.0
        return (self.price / self.prev_close - 1.0) * 100.0


def _select_session_price(info: dict) -> Optional[float]:
    state = info.get("marketState") or ""
    if state == "PRE":
        return info.get("preMarketPrice") or info.get("regularMarketPrice")
    if state in ("POST", "POSTPOST"):
        return info.get("postMarketPrice") or info.get("regularMarketPrice")
    return info.get("regularMarketPrice")


def _quote_one(symbol: str) -> Optional[YahooQuote]:
    try:
        info = yf.Ticker(symbol).info
    except Exception:
        return None
    price = _select_session_price(info)
    rth_price = info.get("regularMarketPrice")
    prev_close = info.get("regularMarketPreviousClose")
    if price is None or rth_price is None or prev_close is None:
        return None
    bid = info.get("bid") or None
    ask = info.get("ask") or None
    if bid == 0:
        bid = None
    if ask == 0:
        ask = None
    return YahooQuote(
        symbol=symbol,
        price=float(price),
        rth_price=float(rth_price),
        prev_close=float(prev_close),
        market_state=str(info.get("marketState") or ""),
        bid=float(bid) if bid is not None else None,
        ask=float(ask) if ask is not None else None,
    )


def fetch_yahoo_quotes(symbols: tuple[str, ...]) -> dict[str, YahooQuote]:
    if not symbols:
        return {}
    key = tuple(sorted(symbols))
    now = time.time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    out: dict[str, YahooQuote] = {}
    with cf.ThreadPoolExecutor(max_workers=min(8, len(symbols))) as ex:
        for sym, q in zip(symbols, ex.map(_quote_one, symbols)):
            if q is not None:
                out[sym] = q
    _CACHE[key] = (now, out)
    return out
