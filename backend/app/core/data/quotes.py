"""Watchlist quotes: Yahoo primary, Alpaca snapshot fallback."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest

from app.core.config import get_settings
from app.core.market import MarketStatus, current_market_state
from app.core.data.yahoo import YahooQuote, fetch_yahoo_quotes

log = logging.getLogger(__name__)

_client_lock = threading.Lock()
_shared_client: Optional[StockHistoricalDataClient] = None
_WL_CACHE: dict[tuple[str, ...], tuple[float, dict[str, YahooQuote]]] = {}
_STALE: dict[str, YahooQuote] = {}
_CACHE_TTL = 15.0


def _alpaca_client() -> Optional[StockHistoricalDataClient]:
    global _shared_client
    settings = get_settings()
    if not settings.has_credentials:
        return None
    with _client_lock:
        if _shared_client is None:
            _shared_client = StockHistoricalDataClient(
                settings.alpaca_api_key,
                settings.alpaca_secret_key,
                url_override=settings.alpaca_data_url_override(),
            )
    return _shared_client


def _session_market_state() -> str:
    mapping = {
        MarketStatus.PRE_MARKET: "PRE",
        MarketStatus.REGULAR: "REGULAR",
        MarketStatus.AFTER_HOURS: "POST",
        MarketStatus.CLOSED: "CLOSED",
    }
    return mapping[current_market_state().status]


def _alpaca_quotes(symbols: tuple[str, ...]) -> dict[str, YahooQuote]:
    client = _alpaca_client()
    if client is None or not symbols:
        return {}
    try:
        snaps = client.get_stock_snapshot(
            StockSnapshotRequest(symbol_or_symbols=list(symbols))
        )
    except Exception as exc:
        log.warning("alpaca snapshot failed: %s", exc)
        return {}

    out: dict[str, YahooQuote] = {}
    for sym, snap in snaps.items():
        lt = getattr(snap, "latest_trade", None)
        db = getattr(snap, "daily_bar", None)
        pdb = getattr(snap, "previous_daily_bar", None)
        lq = getattr(snap, "latest_quote", None)

        price = None
        if lt is not None and getattr(lt, "price", None):
            price = float(lt.price)
        elif db is not None and getattr(db, "close", None):
            price = float(db.close)

        prev_close = None
        if pdb is not None and getattr(pdb, "close", None):
            prev_close = float(pdb.close)

        if price is None or prev_close is None:
            continue

        rth = float(db.close) if db is not None and getattr(db, "close", None) else price
        bid = float(lq.bid_price) if lq is not None and getattr(lq, "bid_price", None) else None
        ask = float(lq.ask_price) if lq is not None and getattr(lq, "ask_price", None) else None

        out[sym] = YahooQuote(
            symbol=sym,
            price=price,
            rth_price=rth,
            prev_close=prev_close,
            market_state=_session_market_state(),
            bid=bid,
            ask=ask,
        )
    return out


def fetch_watchlist_quotes(symbols: tuple[str, ...]) -> dict[str, YahooQuote]:
    """Alpaca batch first (fast); Yahoo only for gaps when not rate-limited."""
    if not symbols:
        return {}

    import time

    key = tuple(sorted(symbols))
    now = time.time()
    cached = _WL_CACHE.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    out = _alpaca_quotes(symbols)
    session = current_market_state()
    # During extended hours, prefer Yahoo session-specific prices when available.
    if session.is_extended:
        yahoo = fetch_yahoo_quotes(symbols)
        for sym, q in yahoo.items():
            out[sym] = q
    else:
        missing = tuple(s for s in symbols if s not in out)
        if missing:
            out.update(fetch_yahoo_quotes(missing))

    for sym in symbols:
        if sym in out:
            _STALE[sym] = out[sym]
        elif sym in _STALE:
            out[sym] = _STALE[sym]

    _WL_CACHE[key] = (now, out)
    return out
