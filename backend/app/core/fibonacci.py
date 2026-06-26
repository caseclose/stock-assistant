"""Fibonacci retracement levels from major swing range."""

from __future__ import annotations

import numpy as np
import pandas as pd

_FIB_RATIOS: tuple[tuple[float, str], ...] = (
    (0.236, "fib_236"),
    (0.382, "fib_382"),
    (0.500, "fib_500"),
    (0.618, "fib_618"),
    (0.786, "fib_786"),
)


def _swing_leg(
    high_idx: np.ndarray,
    low_idx: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
) -> tuple[int, int, float, float, bool] | None:
    """Return (i_lo, i_hi, swing_low, swing_high, uptrend) for the latest completed leg."""

    if len(high_idx) < 1 or len(low_idx) < 1:
        return None

    i_hi_last = int(high_idx[-1])
    i_lo_last = int(low_idx[-1])

    if i_hi_last > i_lo_last:
        # Uptrend leg: low pivot before the high
        prior_lows = low_idx[low_idx < i_hi_last]
        if len(prior_lows) == 0:
            return None
        i_lo = int(prior_lows[-1])
        i_hi = i_hi_last
        uptrend = True
    else:
        # Downtrend leg: high pivot before the low
        prior_highs = high_idx[high_idx < i_lo_last]
        if len(prior_highs) == 0:
            return None
        i_hi = int(prior_highs[-1])
        i_lo = i_lo_last
        uptrend = False

    swing_high = float(highs[i_hi])
    swing_low = float(lows[i_lo])
    if swing_high <= swing_low:
        return None
    return i_lo, i_hi, swing_low, swing_high, uptrend


def fibonacci_candidates(
    sliced: pd.DataFrame,
    close_now: float,
    is_high: np.ndarray,
    is_low: np.ndarray,
) -> list[dict]:
    """Retracement levels from the latest major swing high/low pair."""

    highs = sliced["high"].to_numpy(dtype=float)
    lows = sliced["low"].to_numpy(dtype=float)
    leg = _swing_leg(np.where(is_high)[0], np.where(is_low)[0], highs, lows)
    if leg is None:
        return []

    i_lo, i_hi, swing_low, swing_high, uptrend = leg
    span = swing_high - swing_low
    if span / close_now < 0.02:
        return []

    out: list[dict] = []
    timestamps = sliced.index
    if uptrend:
        for ratio, src in _FIB_RATIOS:
            price = swing_high - span * ratio
            if price <= 0:
                continue
            origin = "low" if price < close_now else "high"
            out.append({
                "price": price,
                "origin": origin,
                "source": src,
                "pivots": 2,
                "weight": 0.45 + (1.0 - abs(ratio - 0.618)) * 0.2,
                "last_touch_idx": i_hi,
                "last_touch_ts": timestamps[i_hi],
                "fib_ratio": ratio,
            })
    else:
        for ratio, src in _FIB_RATIOS:
            price = swing_low + span * ratio
            origin = "high" if price > close_now else "low"
            out.append({
                "price": price,
                "origin": origin,
                "source": src,
                "pivots": 2,
                "weight": 0.45 + (1.0 - abs(ratio - 0.618)) * 0.2,
                "last_touch_idx": i_lo,
                "last_touch_ts": timestamps[i_lo],
                "fib_ratio": ratio,
            })

    return out
