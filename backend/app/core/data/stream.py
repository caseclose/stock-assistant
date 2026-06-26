"""Real-time WebSocket stream → in-memory bar buffer."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.live import StockDataStream

from app.core.config import get_settings
from app.core.rth import bar_gap_minutes, is_regular_hours_bar

log = logging.getLogger(__name__)


@dataclass
class LiveQuote:
    bid: float
    ask: float


class LiveBarBuffer:
    """Append-only rolling DataFrame of OHLCV bars + the latest NBBO quote.

    Reads (``snapshot()``) and writes (from WebSocket callbacks) are guarded
    by a lock so the Streamlit UI thread can sample safely while bars stream
    in on a background thread.

    ``regular_hours_only``: when True (default), drop incoming bars whose
    timestamp is outside 09:30–16:00 NY time. Quotes are always accepted so
    the user still sees a live bid/ask.
    """

    def __init__(
        self,
        symbol: str,
        warmup: pd.DataFrame,
        max_rows: int = 500,
        regular_hours_only: bool = False,
        timeframe_label: str = "1H",
    ):
        self.symbol = symbol
        self._df = warmup.copy()
        self._max_rows = max_rows
        self._lock = threading.Lock()
        self._rth_only = regular_hours_only
        self._timeframe_label = timeframe_label
        self.last_quote: LiveQuote | None = None

    def snapshot(self) -> pd.DataFrame:
        with self._lock:
            return self._df.copy()

    def _gap_minutes(self) -> float:
        with self._lock:
            if len(self._df) >= 2:
                return bar_gap_minutes(self._df.index)
            return {"1Min": 1, "5Min": 5, "15Min": 15, "1H": 60, "1D": 1440}.get(
                self._timeframe_label, 60,
            )

    def _is_regular_hours(self, ts: pd.Timestamp) -> bool:
        return is_regular_hours_bar(ts, gap_min=self._gap_minutes())

    async def on_bar(self, bar) -> None:  # noqa: ANN001 — alpaca Bar model
        ts = pd.Timestamp(bar.timestamp)
        if self._rth_only and not self._is_regular_hours(ts):
            return
        with self._lock:
            row = pd.DataFrame(
                {
                    "open": [bar.open],
                    "high": [bar.high],
                    "low": [bar.low],
                    "close": [bar.close],
                    "volume": [bar.volume],
                },
                index=[ts],
            )
            # If this bar's timestamp matches the last row, overwrite (in case
            # the same minute streams a partial then a final close).
            if not self._df.empty and self._df.index[-1] == row.index[0]:
                self._df.iloc[-1] = row.iloc[0]
            else:
                self._df = pd.concat([self._df, row])
            if len(self._df) > self._max_rows:
                self._df = self._df.iloc[-self._max_rows:]

    async def on_quote(self, quote) -> None:  # noqa: ANN001
        bid = float(getattr(quote, "bid_price", 0) or 0)
        ask = float(getattr(quote, "ask_price", 0) or 0)
        if bid > 0 and ask > 0 and ask >= bid:
            self.last_quote = LiveQuote(bid=bid, ask=ask)


def start_stream(symbol: str, buffer: LiveBarBuffer) -> tuple[threading.Thread, StockDataStream]:
    """Spin up a daemon thread that runs the Alpaca WebSocket forever.

    Returns ``(thread, stream)`` so the caller can later call
    ``stream.stop()`` to release Alpaca's single-connection slot when
    switching tickers — without an explicit stop, the old stream keeps
    holding the slot and a new ``start_stream`` for a different symbol
    gets rejected with "connection limit exceeded".
    """

    settings = get_settings()
    if not settings.has_credentials:
        raise RuntimeError("Alpaca credentials missing; cannot start stream.")

    stream = StockDataStream(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
        feed=DataFeed.IEX,
        url_override=settings.alpaca_data_url_override(),
    )
    stream.subscribe_bars(buffer.on_bar, symbol)
    stream.subscribe_quotes(buffer.on_quote, symbol)

    def _run() -> None:
        # alpaca-py's StockDataStream is asyncio-based; give it its own loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stream.run()
        except Exception:  # pragma: no cover
            log.exception("Alpaca stream crashed; the dashboard will fall back to warm-up data.")

    t = threading.Thread(target=_run, name=f"alpaca-stream-{symbol}", daemon=True)
    t.start()
    return t, stream
