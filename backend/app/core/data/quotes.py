"""Watchlist quotes: Yahoo primary, Alpaca snapshot fallback."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest

from app.core.config import get_settings
from app.core.data.yahoo import YahooQuote, fetch_yahoo_quotes

log = logging.getLogger(__name__)

_client_lock = threading.Lock()
_shared_client: Optional[StockHistoricalDataClient] = None


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
            )
    return _shared_client


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
            market_state="REGULAR",
            bid=bid,
            ask=ask,
        )
    return out


def fetch_watchlist_quotes(symbols: tuple[str, ...]) -> dict[str, YahooQuote]:
    """Yahoo first (ext-hours aware), Alpaca snapshot for any misses."""
    if not symbols:
        return {}
    out = fetch_yahoo_quotes(symbols)
    missing = tuple(s for s in symbols if s not in out)
    if missing:
        out.update(_alpaca_quotes(missing))
    return out
