"""Single-slot Alpaca stream hub for WebSocket clients."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any

from app.core.data import LiveBarBuffer, fetch_warmup_bars, start_stream

log = logging.getLogger(__name__)

_SUBSCRIBE_WARMUP_BARS = 80
_SUBSCRIBE_TIMEOUT_SEC = 25.0
_STREAM_STOP_GRACE_SEC = 0.4


class StreamHub:
    """One Alpaca WS at a time; fan-out bar updates to FastAPI WS clients."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribe_lock = asyncio.Lock()
        self._clients: set[asyncio.Queue] = set()
        self._symbol: str | None = None
        self._interval: str | None = None
        self._extended_hours: bool = True
        self._buffer: LiveBarBuffer | None = None
        self._stream_thread: threading.Thread | None = None
        self._stream: Any = None
        self._poll_task: asyncio.Task | None = None
        self._last_signature: tuple | None = None

    async def subscribe(
        self,
        symbol: str,
        interval: str,
        extended_hours: bool = True,
    ) -> None:
        async with self._subscribe_lock:
            symbol = symbol.upper()
            with self._lock:
                if (
                    self._symbol == symbol
                    and self._interval == interval
                    and self._extended_hours == extended_hours
                    and self._buffer is not None
                ):
                    return

            try:
                warmup = await asyncio.wait_for(
                    asyncio.to_thread(
                        fetch_warmup_bars,
                        symbol,
                        interval,
                        _SUBSCRIBE_WARMUP_BARS,
                        not extended_hours,
                    ),
                    timeout=_SUBSCRIBE_TIMEOUT_SEC,
                )
            except asyncio.TimeoutError:
                log.warning("stream subscribe warmup timed out for %s %s", symbol, interval)
                raise RuntimeError("stream warmup timed out") from None
            except Exception:
                log.exception("warmup fetch failed for %s %s", symbol, interval)
                raise

            buffer = LiveBarBuffer(
                symbol,
                warmup,
                regular_hours_only=not extended_hours,
                timeframe_label=interval,
            )

            with self._lock:
                if (
                    self._symbol == symbol
                    and self._interval == interval
                    and self._extended_hours == extended_hours
                    and self._buffer is not None
                ):
                    return
                self._stop_stream_locked()

            await asyncio.sleep(_STREAM_STOP_GRACE_SEC)

            with self._lock:
                thread, stream = start_stream(symbol, buffer)
                self._symbol = symbol
                self._interval = interval
                self._extended_hours = extended_hours
                self._buffer = buffer
                self._stream_thread = thread
                self._stream = stream
                self._last_signature = None

    def _stop_stream_locked(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
            except Exception:
                log.debug("stream stop failed", exc_info=True)
        self._stream = None
        self._stream_thread = None
        self._buffer = None
        self._symbol = None
        self._interval = None
        self._extended_hours = True
        self._last_signature = None

    def register_client(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=32)
        self._clients.add(q)
        return q

    def unregister_client(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)

    def shutdown(self) -> None:
        with self._lock:
            self._stop_stream_locked()
        self._clients.clear()

    async def _broadcast(self, msg: dict) -> None:
        dead = []
        for q in self._clients:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._clients.discard(q)

    @staticmethod
    def _bar_signature(row, ts) -> tuple:
        return (
            int(pd_timestamp(ts)),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
            float(row["volume"]),
        )

    async def poll_loop(self) -> None:
        while True:
            await asyncio.sleep(1)
            with self._lock:
                if self._buffer is None:
                    continue
                df = self._buffer.snapshot()
                if df.empty:
                    continue
                row = df.iloc[-1]
                ts = df.index[-1]
                sig = self._bar_signature(row, ts)
                if sig == self._last_signature:
                    continue
                self._last_signature = sig
                symbol = self._symbol
                interval = self._interval
            await self._broadcast({
                "type": "bar",
                "symbol": symbol,
                "interval": interval,
                "bar": {
                    "time": sig[0],
                    "open": sig[1],
                    "high": sig[2],
                    "low": sig[3],
                    "close": sig[4],
                    "volume": sig[5],
                },
            })


def pd_timestamp(ts) -> int:
    import pandas as pd
    return int(pd.Timestamp(ts).timestamp())
