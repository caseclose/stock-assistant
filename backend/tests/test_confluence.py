"""Tests for MA confluence and trendlines."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.confluence import ma_confluence, trendline_candidates


def test_ma_confluence_detects_nearby_ma() -> None:
    row = pd.Series({"sma50": 100.0, "ema20": 120.0, "close": 101.0})
    aligned = ma_confluence(100.2, row, atr=1.0)
    assert "SMA50" in aligned
    assert "EMA20" not in aligned


def test_trendline_projects_resistance() -> None:
    n = 40
    highs = np.linspace(100, 110, n)
    lows = highs - 2
    is_high = np.zeros(n, dtype=bool)
    is_low = np.zeros(n, dtype=bool)
    is_high[10] = True
    is_high[25] = True
    is_low[5] = True
    is_low[20] = True
    highs[10], highs[25] = 105.0, 108.0
    lows[5], lows[20] = 98.0, 101.0
    idx = pd.bdate_range(end="2026-06-22", periods=n, freq="B")
    nodes = trendline_candidates(highs, lows, is_high, is_low, idx, close_now=106.0)
    res = [c for c in nodes if c["source"] == "trendline" and c["origin"] == "high"]
    assert res
    assert res[0]["price"] > 106.0
