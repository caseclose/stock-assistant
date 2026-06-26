"""Tests for Fibonacci retracement levels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.fibonacci import fibonacci_candidates
from app.core.levels import _swing_pivots


def test_fibonacci_uptrend_retracements() -> None:
    n = 50
    closes = list(np.linspace(90, 120, n))
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    is_high, is_low = _swing_pivots(np.array(highs), np.array(lows), 2)
    is_low[5] = True
    is_high[-5] = True
    lows[5] = 90.0
    highs[-5] = 120.0
    df = pd.DataFrame(
        {"high": highs, "low": lows, "close": closes, "volume": [1e6] * n},
        index=pd.bdate_range(end="2026-06-22", periods=n, freq="B"),
    )
    cands = fibonacci_candidates(df, close_now=110.0, is_high=is_high, is_low=is_low)
    assert any(c["source"] == "fib_618" for c in cands)
    fib618 = next(c for c in cands if c["source"] == "fib_618")
    assert 100 < fib618["price"] < 115
    assert fib618["pivots"] == 2


def test_fibonacci_downtrend_retracements() -> None:
    n = 50
    closes = list(np.linspace(120, 90, n))
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    is_high, is_low = _swing_pivots(np.array(highs), np.array(lows), 2)
    is_high[5] = True
    is_low[-5] = True
    highs[5] = 120.0
    lows[-5] = 90.0
    df = pd.DataFrame(
        {"high": highs, "low": lows, "close": closes, "volume": [1e6] * n},
        index=pd.bdate_range(end="2026-06-22", periods=n, freq="B"),
    )
    cands = fibonacci_candidates(df, close_now=95.0, is_high=is_high, is_low=is_low)
    assert cands
    assert all(c["price"] > 90 for c in cands)
