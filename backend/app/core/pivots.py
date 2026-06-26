"""Shared swing-pivot helpers for levels and trendlines."""

from __future__ import annotations

import numpy as np


def adaptive_window(atr_ratio: float) -> int:
    """Wider swings in calm markets, tighter in volatile ones."""
    if atr_ratio < 0.012:
        return 4
    if atr_ratio < 0.025:
        return 3
    return 2


def swing_pivots(highs: np.ndarray, lows: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(highs)
    is_high = np.zeros(n, dtype=bool)
    is_low = np.zeros(n, dtype=bool)
    if n < 2 * window + 1:
        return is_high, is_low
    for i in range(window, n - window):
        h = highs[i]
        l = lows[i]
        if h == highs[i - window:i + window + 1].max() and h > highs[i - window:i].max():
            is_high[i] = True
        if l == lows[i - window:i + window + 1].min() and l < lows[i - window:i].min():
            is_low[i] = True
    return is_high, is_low
