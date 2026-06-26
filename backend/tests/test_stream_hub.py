"""Tests for StreamHub bar broadcast and subscribe logic."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.stream_hub import StreamHub


def test_bar_signature_changes_on_inplace_update() -> None:
    ts = pd.Timestamp("2026-06-24 14:00:00", tz="UTC")
    row1 = pd.Series({"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100.0})
    row2 = pd.Series({"open": 1.0, "high": 2.5, "low": 0.5, "close": 2.0, "volume": 150.0})
    sig1 = StreamHub._bar_signature(row1, ts)
    sig2 = StreamHub._bar_signature(row2, ts)
    assert sig1[0] == sig2[0]
    assert sig1 != sig2


def test_subscribe_fetch_failure_preserves_existing_stream() -> None:
    hub = StreamHub()
    old_buffer = MagicMock()
    hub._symbol = "AAPL"
    hub._interval = "1H"
    hub._extended_hours = True
    hub._buffer = old_buffer
    hub._stream = MagicMock()

    with patch("app.services.stream_hub.fetch_warmup_bars", side_effect=RuntimeError("network")):
        with pytest.raises(RuntimeError):
            asyncio.run(hub.subscribe("MSFT", "1H"))

    assert hub._symbol == "AAPL"
    assert hub._buffer is old_buffer
    assert hub._stream is not None


def test_subscribe_switches_after_successful_fetch() -> None:
    hub = StreamHub()
    hub._symbol = "AAPL"
    hub._interval = "1H"
    hub._buffer = MagicMock()
    hub._stream = MagicMock()

    warmup = pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100.0]},
        index=pd.DatetimeIndex([pd.Timestamp("2026-06-24 14:00:00", tz="UTC")]),
    )
    new_stream = MagicMock()
    new_thread = MagicMock()

    with (
        patch("app.services.stream_hub.fetch_warmup_bars", return_value=warmup),
        patch("app.services.stream_hub.start_stream", return_value=(new_thread, new_stream)),
    ):
        asyncio.run(hub.subscribe("MSFT", "15Min", extended_hours=False))

    assert hub._symbol == "MSFT"
    assert hub._interval == "15Min"
    assert hub._extended_hours is False
    assert hub._stream is new_stream
