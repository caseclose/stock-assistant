"""Tests for support / resistance level detection."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.levels import LevelKind, compute_levels, lookback_bars_for_freq


def _make_bars(highs, lows, closes=None) -> pd.DataFrame:
    n = len(highs)
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    opens = closes.copy()
    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [1_000_000] * n,
            "atr": [1.0] * n,
        },
        index=pd.bdate_range(end="2026-06-22", periods=n, freq="B"),
    )


def test_no_levels_when_too_few_bars() -> None:
    df = _make_bars([100, 101, 102], [99, 99.5, 100])
    assert compute_levels(df, window=3) == []


def test_detects_repeated_resistance_at_same_price() -> None:
    pattern = []
    for _ in range(3):
        pattern += [100, 102, 105, 108, 110, 109, 106, 102]
    closes = pattern
    highs = [c + 0.4 for c in closes]
    lows = [c - 0.4 for c in closes]
    highs[-1] = 102.2
    lows[-1] = 101.7
    closes[-1] = 102.0
    df = _make_bars(highs, lows, closes)
    levels = compute_levels(df, window=2, min_touches=2)
    resistances = [lv for lv in levels if lv.kind is LevelKind.RESISTANCE]
    assert resistances
    top = resistances[0]
    assert 108 <= top.price <= 112
    assert top.touches >= 2
    assert top.pivots >= 2
    assert top.distance_pct > 0


def test_detects_repeated_support() -> None:
    pattern = []
    for _ in range(3):
        pattern += [100, 98, 95, 92, 90, 91, 94, 98]
    closes = pattern
    highs = [c + 0.4 for c in closes]
    lows = [c - 0.4 for c in closes]
    highs[-1] = 99.2
    lows[-1] = 98.7
    closes[-1] = 99.0
    df = _make_bars(highs, lows, closes)
    levels = compute_levels(df, window=2, min_touches=2)
    supports = [lv for lv in levels if lv.kind is LevelKind.SUPPORT]
    assert supports
    top = supports[0]
    assert 88 <= top.price <= 92
    assert top.touches >= 2
    assert top.distance_pct < 0


def test_retests_exceed_pivots_on_repeated_pattern() -> None:
    pattern = []
    for _ in range(3):
        pattern += [100, 102, 105, 108, 110, 109, 106, 102]
    closes = pattern
    highs = [c + 0.4 for c in closes]
    lows = [c - 0.4 for c in closes]
    closes[-1] = 102.0
    df = _make_bars(highs, lows, closes)
    levels = compute_levels(df, window=2, min_touches=2)
    resistances = [lv for lv in levels if lv.kind is LevelKind.RESISTANCE]
    assert resistances
    assert resistances[0].touches >= resistances[0].pivots


def test_intraday_uses_daily_source_for_levels() -> None:
    intra_closes = [100.0] * 50 + [102.0]
    intra = _make_bars(
        [c + 0.2 for c in intra_closes],
        [c - 0.2 for c in intra_closes],
        intra_closes,
    )
    daily_pattern = []
    for _ in range(3):
        daily_pattern += [100, 105, 115, 120, 115, 105]
    daily_closes = daily_pattern + [105]
    daily = _make_bars(
        [c + 0.5 for c in daily_closes],
        [c - 0.5 for c in daily_closes],
        daily_closes,
    )
    levels = compute_levels(
        intra, trade_freq="1H", daily_df=daily, window=2, min_touches=2,
    )
    resistances = [lv for lv in levels if lv.kind is LevelKind.RESISTANCE]
    assert resistances
    assert 118 <= resistances[0].price <= 122


def test_lookback_scales_with_freq() -> None:
    assert lookback_bars_for_freq("1D", 500) == 250
    assert lookback_bars_for_freq("1H", 5000) == 1638
    assert lookback_bars_for_freq("1Min", 100) == 100


def test_min_touches_filters_one_off_pivots() -> None:
    rng = np.random.default_rng(7)
    n = 80
    closes = list(100 + rng.normal(scale=1.0, size=n).cumsum() * 0.1)
    highs = [c + 0.3 for c in closes]
    lows = [c - 0.3 for c in closes]
    df = _make_bars(highs, lows, closes)
    levels = compute_levels(df, window=3, min_touches=3)
    for lv in levels:
        assert lv.touches >= 3
