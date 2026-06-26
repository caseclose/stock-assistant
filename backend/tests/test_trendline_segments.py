"""Tests for diagonal trendline segments."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.trendlines import compute_trendline_segments


def test_trendline_segment_has_endpoints() -> None:
    n = 50
    highs = np.linspace(100, 115, n)
    lows = highs - 2
    highs[12] = 108.0
    highs[30] = 112.0
    lows[8] = 98.0
    lows[28] = 102.0
    df = pd.DataFrame(
        {
            "high": highs,
            "low": lows,
            "close": (highs + lows) / 2,
            "volume": [1e6] * n,
            "atr": [1.0] * n,
        },
        index=pd.bdate_range(end="2026-06-22", periods=n, freq="B"),
    )
    segs = compute_trendline_segments(df, close_now=113.0, window=2)
    assert segs
    tl = segs[0]
    assert tl.t1 < tl.t2 <= tl.t_end
    assert tl.p_end > 0
