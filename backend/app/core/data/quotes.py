"""Watchlist quotes: Alpaca snapshot primary, Yahoo fallback for gaps."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest

from app.core.config import get_settings
from app.core.market import (
    NY,
    MarketStatus,
    clock_session_label,
    current_market_state,
    session_label_for_ny_time,
)
from app.core.data.historical import fetch_latest_bar_quote
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


def _ts_ny(obj: Any) -> Optional[datetime]:
    ts = getattr(obj, "timestamp", None)
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(NY)


def _quote_mid(lq: Any) -> Optional[float]:
    bid = getattr(lq, "bid_price", None)
    ask = getattr(lq, "ask_price", None)
    if bid and ask and float(bid) > 0 and float(ask) > 0:
        return (float(bid) + float(ask)) / 2.0
    if bid and float(bid) > 0:
        return float(bid)
    if ask and float(ask) > 0:
        return float(ask)
    return None


def resolve_snapshot_quote(snap: Any) -> Optional[tuple[float, str, float]]:
    """Pick display price and the session it belongs to (not wall-clock session).

    Returns (price, market_state, rth_price).
    """

    lt = getattr(snap, "latest_trade", None)
    db = getattr(snap, "daily_bar", None)
    pdb = getattr(snap, "previous_daily_bar", None)
    lq = getattr(snap, "latest_quote", None)

    rth = float(db.close) if db is not None and getattr(db, "close", None) else None
    prev_daily = float(pdb.close) if pdb is not None and getattr(pdb, "close", None) else None

    trade_price = float(lt.price) if lt is not None and getattr(lt, "price", None) else None
    trade_sess = None
    if lt is not None:
        trade_ny = _ts_ny(lt)
        if trade_ny is not None:
            trade_sess = session_label_for_ny_time(trade_ny)

    quote_mid = _quote_mid(lq) if lq is not None else None
    quote_sess = None
    if lq is not None:
        quote_ny = _ts_ny(lq)
        if quote_ny is not None:
            quote_sess = session_label_for_ny_time(quote_ny)

    clock_sess = clock_session_label(current_market_state().status)

    if clock_sess == "PRE":
        if trade_sess == "PRE" and trade_price is not None:
            return trade_price, "PRE", rth or trade_price
        if quote_sess == "PRE" and quote_mid is not None:
            return quote_mid, "PRE", rth or quote_mid
        if rth is not None:
            return rth, "REGULAR", rth
    elif clock_sess == "REGULAR":
        if trade_price is not None and trade_sess in ("REGULAR", "PRE"):
            sess = "REGULAR" if trade_sess == "PRE" else trade_sess
            return trade_price, sess, rth or trade_price
        if rth is not None:
            return rth, "REGULAR", rth
    elif clock_sess == "POST":
        if trade_sess == "POST" and trade_price is not None:
            return trade_price, "POST", rth or trade_price
        if trade_price is not None:
            return trade_price, trade_sess or "POST", rth or trade_price
    else:
        if trade_price is not None:
            return trade_price, trade_sess or "CLOSED", rth or trade_price
        if prev_daily is not None:
            return prev_daily, "CLOSED", rth or prev_daily

    if trade_price is not None:
        return trade_price, trade_sess or clock_sess, rth or trade_price
    if rth is not None:
        return rth, "REGULAR", rth
    return None


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
        pdb = getattr(snap, "previous_daily_bar", None)
        lq = getattr(snap, "latest_quote", None)

        resolved = resolve_snapshot_quote(snap)
        if resolved is None:
            continue
        price, market_state, rth = resolved

        prev_close = None
        if pdb is not None and getattr(pdb, "close", None):
            prev_close = float(pdb.close)
        if prev_close is None:
            continue

        bid = float(lq.bid_price) if lq is not None and getattr(lq, "bid_price", None) else None
        ask = float(lq.ask_price) if lq is not None and getattr(lq, "ask_price", None) else None

        out[sym] = YahooQuote(
            symbol=sym,
            price=price,
            rth_price=rth,
            prev_close=prev_close,
            market_state=market_state,
            bid=bid,
            ask=ask,
        )
    return out


def _normalize_market_state(raw: str) -> str:
    state = (raw or "").upper()
    if state in ("PRE", "PREMARKET", "PRE_MARKET"):
        return "PRE"
    if state in ("REGULAR", "REGULAR_MARKET"):
        return "REGULAR"
    if state in ("POST", "POSTPOST", "AFTER_HOURS", "AFTERHOURS"):
        return "POST"
    if state in ("CLOSED", "CLOSE"):
        return "CLOSED"
    return state or "CLOSED"


def _refresh_with_bar_quote(sym: str, q: YahooQuote) -> YahooQuote:
    """During pre-market, replace stale snapshot prices with recent bar close."""

    clock_sess = clock_session_label(current_market_state().status)
    if clock_sess != "PRE":
        return q
    if _normalize_market_state(q.market_state) == "PRE":
        return q

    bar = fetch_latest_bar_quote(sym)
    if bar is None:
        return q
    price, bar_sess = bar
    if bar_sess != "PRE":
        return q
    return YahooQuote(
        symbol=q.symbol,
        price=price,
        rth_price=q.rth_price,
        prev_close=q.prev_close,
        market_state="PRE",
        bid=q.bid,
        ask=q.ask,
    )


def fetch_watchlist_quotes(symbols: tuple[str, ...]) -> dict[str, YahooQuote]:
    """Alpaca batch first; Yahoo fills gaps. Pre-market prefers fresher sources."""
    if not symbols:
        return {}

    import time

    key = tuple(sorted(symbols))
    now = time.time()
    cached = _WL_CACHE.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    clock = current_market_state()
    pre_market = clock.status == MarketStatus.PRE_MARKET

    if pre_market:
        yahoo = fetch_yahoo_quotes(symbols)
        alpaca = _alpaca_quotes(symbols)
        out: dict[str, YahooQuote] = {}
        for sym in symbols:
            yq = yahoo.get(sym)
            aq = alpaca.get(sym)
            if yq is not None and _normalize_market_state(yq.market_state) == "PRE":
                out[sym] = yq
            elif aq is not None:
                out[sym] = _refresh_with_bar_quote(sym, aq)
            elif yq is not None:
                out[sym] = yq
    else:
        out = _alpaca_quotes(symbols)
        missing = tuple(s for s in symbols if s not in out)
        if missing:
            out.update(fetch_yahoo_quotes(missing))

    for sym in symbols:
        if sym in out:
            out[sym] = _refresh_with_bar_quote(sym, out[sym])
            _STALE[sym] = out[sym]
        elif sym in _STALE:
            out[sym] = _STALE[sym]

    _WL_CACHE[key] = (now, out)
    return out
