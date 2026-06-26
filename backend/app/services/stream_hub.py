"""Single-slot Alpaca stream hub for WebSocket clients."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any

from app.core.data import LiveBarBuffer, fetch_warmup_bars, start_stream

log = logging.getLogger(__name__)


class StreamHub:
    """One Alpaca WS at a time; fan-out bar updates to FastAPI WS clients."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: set[asyncio.Queue] = set()
        self._symbol: str | None = None
        self._interval: str | None = None
        self._buffer: LiveBarBuffer | None = None
        self._stream_thread: threading.Thread | None = None
        self._stream: Any = None
        self._poll_task: asyncio.Task | None = None
        self._last_len = 0

    async def subscribe(self, symbol: str, interval: str) -> None:
        symbol = symbol.upper()
        with self._lock:
            if self._symbol == symbol and self._interval == interval:
                return
            self._stop_stream_locked()
            warmup = fetch_warmup_bars(symbol, interval, limit=200)
            buffer = LiveBarBuffer(symbol, warmup)
            thread, stream = start_stream(symbol, buffer)
            self._symbol = symbol
            self._interval = interval
            self._buffer = buffer
            self._stream_thread = thread
            self._stream = stream
            self._last_len = len(buffer.snapshot())

    def _stop_stream_locked(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
            except Exception:
                pass
        self._stream = None
        self._stream_thread = None
        self._buffer = None
        self._symbol = None
        self._interval = None
        self._last_len = 0

    def register_client(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=32)
        self._clients.add(q)
        return q

    def unregister_client(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)

    async def _broadcast(self, msg: dict) -> None:
        dead = []
        for q in self._clients:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._clients.discard(q)

    async def poll_loop(self) -> None:
        while True:
            await asyncio.sleep(2)
            with self._lock:
                if self._buffer is None:
                    continue
                df = self._buffer.snapshot()
                n = len(df)
                if n == 0 or n == self._last_len:
                    continue
                row = df.iloc[-1]
                ts = df.index[-1]
                self._last_len = n
            await self._broadcast({
                "type": "bar",
                "symbol": self._symbol,
                "interval": self._interval,
                "bar": {
                    "time": int(pd_timestamp(ts)),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                },
            })


def pd_timestamp(ts) -> int:
    import pandas as pd
    return int(pd.Timestamp(ts).timestamp())
