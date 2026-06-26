"""MA confluence and projected trendline levels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.trendlines import trendline_level_candidates

_MA_COLS: tuple[tuple[str, str], ...] = (
    ("sma20", "SMA20"),
    ("sma50", "SMA50"),
    ("sma60", "SMA60"),
    ("sma120", "SMA120"),
    ("sma200", "SMA200"),
    ("ema20", "EMA20"),
    ("ema50", "EMA50"),
)


def ma_confluence(price: float, row: pd.Series, atr: float) -> list[str]:
    """MAs within ``0.35 * ATR`` of the level price."""

    tol = max(atr * 0.35, price * 0.001)
    aligned: list[str] = []
    for col, label in _MA_COLS:
        val = row.get(col)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        if abs(float(val) - price) <= tol:
            aligned.append(label)
    return aligned


def trendline_candidates(
    highs: np.ndarray,
    lows: np.ndarray,
    is_high: np.ndarray,
    is_low: np.ndarray,
    timestamps: pd.DatetimeIndex,
    close_now: float,
) -> list[dict]:
    """Project resistance/support trendlines from the last two swing pivots."""

    return trendline_level_candidates(
        highs, lows, is_high, is_low, timestamps, close_now,
    )


def ma_level_candidates(
    row: pd.Series,
    close_now: float,
    last_ts: pd.Timestamp,
    *,
    max_dist_pct: float = 15.0,
) -> list[dict]:
    """Moving averages as near-term horizontal S/R when within ``max_dist_pct`` of price."""

    out: list[dict] = []
    for col, _label in _MA_COLS:
        val = row.get(col)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        price = float(val)
        dist_pct = abs(price / close_now - 1.0) * 100.0
        if dist_pct > max_dist_pct:
            continue
        origin = "low" if price < close_now else "high"
        out.append({
            "price": price,
            "origin": origin,
            "source": f"ma_{col}",
            "pivots": 1,
            "weight": 0.48,
            "last_touch_idx": None,
            "last_touch_ts": last_ts,
        })
    return out
