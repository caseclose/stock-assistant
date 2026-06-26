"""Tests for level backtest calibration."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.level_backtest import calibrate_strength, walkforward_hit_rate


def _pattern_df() -> pd.DataFrame:
    pattern = []
    for _ in range(4):
        pattern += [100, 102, 105, 108, 110, 109, 106, 102]
    closes = pattern
    highs = [c + 0.4 for c in closes]
    lows = [c - 0.4 for c in closes]
    return pd.DataFrame(
        {"high": highs, "low": lows, "close": closes, "volume": [1_000_000] * len(closes)},
        index=pd.bdate_range(end="2026-06-22", periods=len(closes), freq="B"),
    )


def test_walkforward_hit_rate_on_repeated_resistance() -> None:
    df = _pattern_df()
    rate = walkforward_hit_rate(df, 110.0, 0.5, "high")
    assert rate is not None
    assert rate >= 50.0


def test_calibrate_strength_boosts_ma_confluence() -> None:
    base = calibrate_strength(60.0, bounce_rate=None, hit_rate=None, ma_aligned=[])
    boosted = calibrate_strength(60.0, bounce_rate=None, hit_rate=None, ma_aligned=["SMA50", "EMA20"])
    assert boosted > base
