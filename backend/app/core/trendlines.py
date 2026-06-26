"""Diagonal trendline segments for chart overlay and horizontal level candidates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.pivots import adaptive_window as _adaptive_window
from app.core.pivots import swing_pivots as _swing_pivots


@dataclass
class TrendlineSegment:
    kind: str
    t1: int
    p1: float
    t2: int
    p2: float
    t_end: int
    p_end: float
    strength: float


def _ts_unix(ts: pd.Timestamp) -> int:
    return int(pd.Timestamp(ts).timestamp())


def _line_price_at(i1: int, p1: float, i2: int, p2: float, i: int) -> float:
    if i2 == i1:
        return p2
    slope = (p2 - p1) / (i2 - i1)
    return p1 + slope * (i - i1)


def _last_pivot_pairs(
    highs: np.ndarray,
    lows: np.ndarray,
    is_high: np.ndarray,
    is_low: np.ndarray,
) -> list[tuple[str, int, int, float, float]]:
    pairs: list[tuple[str, int, int, float, float]] = []
    high_idx = np.where(is_high)[0]
    if len(high_idx) >= 2:
        i1, i2 = int(high_idx[-2]), int(high_idx[-1])
        if i2 > i1:
            pairs.append(("high", i1, i2, float(highs[i1]), float(highs[i2])))
    low_idx = np.where(is_low)[0]
    if len(low_idx) >= 2:
        i1, i2 = int(low_idx[-2]), int(low_idx[-1])
        if i2 > i1:
            pairs.append(("low", i1, i2, float(lows[i1]), float(lows[i2])))
    return pairs


def trendline_level_candidates(
    highs: np.ndarray,
    lows: np.ndarray,
    is_high: np.ndarray,
    is_low: np.ndarray,
    timestamps: pd.DatetimeIndex,
    close_now: float,
    *,
    max_dist_pct: float = 0.15,
) -> list[dict]:
    """Project resistance/support trendlines from the last two swing pivots."""

    n = len(highs)
    out: list[dict] = []
    for origin, i1, i2, p1, p2 in _last_pivot_pairs(highs, lows, is_high, is_low):
        projected = _line_price_at(i1, p1, i2, p2, n - 1)
        if origin == "high":
            if projected > close_now and (projected - close_now) / close_now < max_dist_pct:
                out.append({
                    "price": projected,
                    "origin": origin,
                    "source": "trendline",
                    "pivots": 2,
                    "weight": 0.55,
                    "last_touch_idx": i2,
                    "last_touch_ts": timestamps[i2],
                })
        elif projected < close_now and (close_now - projected) / close_now < max_dist_pct:
            out.append({
                "price": projected,
                "origin": origin,
                "source": "trendline",
                "pivots": 2,
                "weight": 0.55,
                "last_touch_idx": i2,
                "last_touch_ts": timestamps[i2],
            })
    return out


def _count_trendline_touches(
    indices: np.ndarray,
    prices: np.ndarray,
    i1: int,
    p1: float,
    i2: int,
    p2: float,
    *,
    tol: float,
) -> int:
    count = 0
    for idx in indices:
        expected = _line_price_at(i1, p1, i2, p2, int(idx))
        if abs(float(prices[int(idx)]) - expected) <= tol:
            count += 1
    return count


def compute_trendline_segments(
    sliced: pd.DataFrame,
    close_now: float,
    *,
    window: int | None = None,
    t_end_override: int | None = None,
) -> list[TrendlineSegment]:
    if sliced.empty or len(sliced) < 10:
        return []

    highs = sliced["high"].to_numpy(dtype=float)
    lows = sliced["low"].to_numpy(dtype=float)
    atr = float(sliced["atr"].iloc[-1]) if "atr" in sliced.columns and not np.isnan(sliced["atr"].iloc[-1]) else close_now * 0.005
    tol = atr * 0.6
    win = window if window is not None else _adaptive_window(atr / max(close_now, 1e-9))
    is_high, is_low = _swing_pivots(highs, lows, win)
    timestamps = sliced.index
    n = len(highs)
    t_end = t_end_override if t_end_override is not None else _ts_unix(timestamps[-1])
    out: list[TrendlineSegment] = []

    for origin, i1, i2, p1, p2 in _last_pivot_pairs(highs, lows, is_high, is_low):
        p_proj = _line_price_at(i1, p1, i2, p2, n - 1)
        if origin == "high":
            if not (p_proj > close_now * 0.98 and (p_proj - close_now) / close_now < 0.15):
                continue
            touches = _count_trendline_touches(np.where(is_high)[0], highs, i1, p1, i2, p2, tol=tol)
            out.append(TrendlineSegment(
                kind="resistance",
                t1=_ts_unix(timestamps[i1]),
                p1=p1,
                t2=_ts_unix(timestamps[i2]),
                p2=p2,
                t_end=t_end,
                p_end=round(p_proj, 2),
                strength=round(min(100.0, 45.0 + touches * 8.0), 1),
            ))
        elif p_proj < close_now * 1.02 and (close_now - p_proj) / close_now < 0.15:
            touches = _count_trendline_touches(np.where(is_low)[0], lows, i1, p1, i2, p2, tol=tol)
            out.append(TrendlineSegment(
                kind="support",
                t1=_ts_unix(timestamps[i1]),
                p1=p1,
                t2=_ts_unix(timestamps[i2]),
                p2=p2,
                t_end=t_end,
                p_end=round(p_proj, 2),
                strength=round(min(100.0, 45.0 + touches * 8.0), 1),
            ))

    return out
