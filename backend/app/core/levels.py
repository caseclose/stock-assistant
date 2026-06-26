"""Support / resistance level detection.

Approach (deliberately simple, deterministic, and fast):

1. **Swing pivots**: local highs/lows in a ``2*window+1`` bar neighbourhood.
2. **Cluster**: pivots within ``cluster_atr_mult * ATR`` merge into one price.
3. **Retest count**: bars whose range intersects the level band (what traders
   usually mean by "touched 3 times").
4. **Split**: above reference close → resistance; below → support.

Intraday charts (``1Min`` … ``1H``) should pass a **daily** enriched frame via
``daily_df`` so levels reflect ~1 year of structure, while distance-to-price
uses the live intraday close.

This is not volume profile / fib / trendlines — horizontal levels only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

# Sub-daily presets: target ~same calendar depth before capping to available bars.
_LOOKBACK_TARGET: dict[str, int] = {
    "1D": 250,       # ~1 trading year
    "1H": 1638,      # ~1 year of RTH hours (252 × 6.5)
    "15Min": 1638,   # ~3 months of RTH 15m bars
    "5Min": 780,     # ~2 weeks
    "1Min": 390,     # ~1 RTH session (fallback when no daily_df)
    "10s": 200,
}
_SUB_DAILY_FREQS = frozenset({"10s", "1Min", "5Min", "15Min", "1H"})


class LevelKind(str, Enum):
    SUPPORT = "support"
    RESISTANCE = "resistance"


@dataclass
class Level:
    price: float
    kind: LevelKind
    touches: int           # bars whose range retested the level (user-facing)
    pivots: int            # swing pivots merged into the cluster
    strength: float        # 0-100 composite score (recency-weighted)
    last_touch: pd.Timestamp
    distance_pct: float    # signed % from reference price (positive = above)


def _median_bar_seconds(index: pd.DatetimeIndex) -> float:
    gaps = index.to_series().diff().dt.total_seconds().dropna()
    return float(gaps.median()) if not gaps.empty else 86_400.0


def _is_sub_daily(trade_freq: str | None, bar_seconds: float) -> bool:
    if trade_freq in _SUB_DAILY_FREQS:
        return True
    return bar_seconds < 70_000  # shorter than ~daily


def lookback_bars_for_freq(trade_freq: str | None, available: int) -> int:
    """How many bars to scan on the active timeframe (capped by ``available``)."""
    target = _LOOKBACK_TARGET.get(trade_freq or "1D", 250)
    return min(max(target, 1), available)


def _swing_pivots(highs: np.ndarray, lows: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
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


def _count_retests(highs: np.ndarray, lows: np.ndarray, price: float, tol: float) -> int:
    """Bars whose high/low range intersects ``[price ± tol]``."""
    band_lo, band_hi = price - tol, price + tol
    return int(((lows <= band_hi) & (highs >= band_lo)).sum())


def _cluster_pivots(
    pivot_prices: np.ndarray,
    pivot_indices: np.ndarray,
    timestamps: pd.DatetimeIndex,
    tolerance: float,
    total_bars: int,
) -> list[dict]:
    clusters: list[dict] = []
    order = np.argsort(pivot_indices)
    for k in order:
        price = float(pivot_prices[k])
        idx = int(pivot_indices[k])
        ts = timestamps[idx]
        recency = 0.2 + 0.8 * (idx / max(1, total_bars - 1))
        merged = False
        for c in clusters:
            if abs(price - c["price"]) <= tolerance:
                new_total_w = c["weight"] + recency
                c["price"] = (c["price"] * c["weight"] + price * recency) / new_total_w
                c["weight"] = new_total_w
                c["pivots"] += 1
                c["last_touch_idx"] = idx
                c["last_touch_ts"] = ts
                merged = True
                break
        if not merged:
            clusters.append({
                "price": price,
                "weight": recency,
                "pivots": 1,
                "last_touch_idx": idx,
                "last_touch_ts": ts,
            })
    return clusters


def _levels_from_slice(
    sliced: pd.DataFrame,
    close_now: float,
    *,
    window: int,
    cluster_atr_mult: float,
    top_n: int,
    min_touches: int,
    min_pivots: int,
) -> list[Level]:
    highs = sliced["high"].to_numpy(dtype=float)
    lows = sliced["low"].to_numpy(dtype=float)

    if "atr" in sliced.columns and not np.isnan(sliced["atr"].iloc[-1]):
        atr_now = float(sliced["atr"].iloc[-1])
    else:
        atr_now = close_now * 0.005

    is_high, is_low = _swing_pivots(highs, lows, window)
    if not is_high.any() and not is_low.any():
        return []

    tol = cluster_atr_mult * atr_now
    timestamps = sliced.index

    high_clusters = _cluster_pivots(
        highs[is_high], np.where(is_high)[0], timestamps, tol, len(sliced),
    )
    low_clusters = _cluster_pivots(
        lows[is_low], np.where(is_low)[0], timestamps, tol, len(sliced),
    )

    for c in high_clusters + low_clusters:
        c["retests"] = _count_retests(highs, lows, c["price"], tol)

    def _score(c: dict) -> float:
        t = min(c["retests"], 12)
        touch_pts = min(50, max(0, (t - 1) * 10))
        last_rel = c["last_touch_idx"] / max(1, len(sliced) - 1)
        recency_pts = 30 * (last_rel ** 0.5)
        weight_pts = min(20, c["weight"] * 5)
        pivot_pts = min(10, max(0, (c["pivots"] - 1) * 4))
        return touch_pts + recency_pts + weight_pts + pivot_pts

    def _eligible(c: dict) -> bool:
        return c["pivots"] >= min_pivots and c["retests"] >= min_touches

    above = [c for c in high_clusters if c["price"] > close_now and _eligible(c)]
    below = [c for c in low_clusters if c["price"] < close_now and _eligible(c)]
    above.sort(key=_score, reverse=True)
    below.sort(key=_score, reverse=True)

    levels: list[Level] = []
    for c in above[:top_n]:
        levels.append(Level(
            price=round(c["price"], 2),
            kind=LevelKind.RESISTANCE,
            touches=c["retests"],
            pivots=c["pivots"],
            strength=round(min(100.0, _score(c)), 1),
            last_touch=c["last_touch_ts"],
            distance_pct=round((c["price"] / close_now - 1.0) * 100.0, 2),
        ))
    for c in below[:top_n]:
        levels.append(Level(
            price=round(c["price"], 2),
            kind=LevelKind.SUPPORT,
            touches=c["retests"],
            pivots=c["pivots"],
            strength=round(min(100.0, _score(c)), 1),
            last_touch=c["last_touch_ts"],
            distance_pct=round((c["price"] / close_now - 1.0) * 100.0, 2),
        ))
    levels.sort(key=lambda lv: (lv.kind.value, abs(lv.distance_pct)))
    return levels


def compute_levels(
    df: pd.DataFrame,
    *,
    window: int = 3,
    cluster_atr_mult: float = 0.5,
    top_n: int = 3,
    min_touches: int = 2,
    min_pivots: int = 2,
    lookback_bars: int | None = None,
    trade_freq: str | None = None,
    daily_df: pd.DataFrame | None = None,
    reference_close: float | None = None,
) -> list[Level]:
    """Detect horizontal support / resistance levels.

    ``df`` must contain OHLC; ``atr`` from ``compute_all`` is recommended.

    For intraday ``trade_freq``, pass ``daily_df`` (also enriched) so levels
    are anchored on ~1y of daily structure. ``reference_close`` defaults to the
    last close of ``df`` (live intraday price).
    """

    if df.empty or len(df) < window * 2 + 2:
        return []

    close_now = float(reference_close if reference_close is not None else df["close"].iloc[-1])
    bar_seconds = _median_bar_seconds(df.index)

    source = df
    source_lookback = lookback_bars
    if (
        daily_df is not None
        and not daily_df.empty
        and len(daily_df) >= window * 2 + 2
        and _is_sub_daily(trade_freq, bar_seconds)
    ):
        source = daily_df
        source_lookback = lookback_bars if lookback_bars is not None else _LOOKBACK_TARGET["1D"]
    elif lookback_bars is None:
        source_lookback = lookback_bars_for_freq(trade_freq, len(df))

    if source_lookback is None:
        source_lookback = 250
    sliced = source.tail(min(source_lookback, len(source))).copy()
    if len(sliced) < window * 2 + 2:
        return []

    return _levels_from_slice(
        sliced,
        close_now,
        window=window,
        cluster_atr_mult=cluster_atr_mult,
        top_n=top_n,
        min_touches=min_touches,
        min_pivots=min_pivots,
    )
