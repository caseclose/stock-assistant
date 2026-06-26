"""Support / resistance level detection (trader-grade horizontal levels).

Pipeline:

1. **Swing pivots** on structure timeframe (daily for intraday charts).
2. **Volume profile** nodes: POC, value-area high/low.
3. **Psychological** round-number magnets near price.
4. **Cluster** nearby candidates within ``cluster_atr_mult * ATR``.
5. **Score** with volume-weighted retests, recency, bounce-rate history.
6. **Role flip**: broken support → overhead resistance (and vice versa).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

from app.core.confluence import ma_confluence, trendline_candidates
from app.core.fibonacci import fibonacci_candidates
from app.core.level_backtest import calibrate_strength, source_bonus, walkforward_hit_rate
from app.core.pivots import adaptive_window as _adaptive_window
from app.core.pivots import swing_pivots as _swing_pivots
from app.core.volume_profile import volume_profile_nodes

_LOOKBACK_TARGET: dict[str, int] = {
    "1D": 250,
    "1H": 1638,
    "15Min": 1638,
    "5Min": 780,
    "1Min": 390,
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
    touches: int
    pivots: int
    strength: float
    last_touch: pd.Timestamp
    distance_pct: float
    source: str = "swing"
    origin: str = "high"
    flipped: bool = False
    bounce_rate: float | None = None
    volume_score: float = 0.0
    hit_rate: float | None = None
    ma_aligned: list[str] = field(default_factory=list)


def _median_bar_seconds(index: pd.DatetimeIndex) -> float:
    gaps = index.to_series().diff().dt.total_seconds().dropna()
    return float(gaps.median()) if not gaps.empty else 86_400.0


def _is_sub_daily(trade_freq: str | None, bar_seconds: float) -> bool:
    if trade_freq in _SUB_DAILY_FREQS:
        return True
    return bar_seconds < 70_000


def lookback_bars_for_freq(trade_freq: str | None, available: int) -> int:
    target = _LOOKBACK_TARGET.get(trade_freq or "1D", 250)
    return min(max(target, 1), available)


def _retest_stats(
    sliced: pd.DataFrame,
    price: float,
    tol: float,
    origin: str,
) -> dict:
    """Volume-weighted retests + historical hold/bounce rate at this band."""
    highs = sliced["high"].to_numpy(dtype=float)
    lows = sliced["low"].to_numpy(dtype=float)
    closes = sliced["close"].to_numpy(dtype=float)
    volumes = sliced["volume"].to_numpy(dtype=float) if "volume" in sliced.columns else np.ones(len(sliced))
    band_lo, band_hi = price - tol, price + tol
    touch_mask = (lows <= band_hi) & (highs >= band_lo)
    touches = int(touch_mask.sum())
    touch_vol = float(volumes[touch_mask].sum()) if touches else 0.0
    avg_vol = float(volumes.mean()) if len(volumes) else 1.0
    volume_score = min(100.0, (touch_vol / max(avg_vol * max(touches, 1), 1e-9)) * 25.0)

    touch_idx = np.where(touch_mask)[0]
    holds = 0
    breaks = 0
    for i in touch_idx:
        if i >= len(sliced) - 3:
            continue
        forward = closes[i + 1:i + 4]
        if origin == "high":
            if np.any(forward > price + tol):
                breaks += 1
            elif np.any(forward < price - tol):
                holds += 1
        else:
            if np.any(forward < price - tol):
                breaks += 1
            elif np.any(forward > price + tol):
                holds += 1
    bounce_rate = None
    if holds + breaks > 0:
        bounce_rate = round(100.0 * holds / (holds + breaks), 1)

    last_touch_idx = int(touch_idx[-1]) if len(touch_idx) else None
    last_touch_ts = sliced.index[last_touch_idx] if last_touch_idx is not None else sliced.index[-1]
    return {
        "retests": touches,
        "volume_score": volume_score,
        "bounce_rate": bounce_rate,
        "last_touch_idx": last_touch_idx,
        "last_touch_ts": last_touch_ts,
    }


def _sustained_break(closes: np.ndarray, price: float, tol: float, *, upward: bool) -> bool:
    """Two consecutive closes beyond the band = structural break."""
    if upward:
        mask = closes > price + tol
    else:
        mask = closes < price - tol
    if len(mask) < 2:
        return False
    return bool(np.any(mask[1:] & mask[:-1]))


def _assign_kind(
    origin: str,
    price: float,
    close_now: float,
    closes: np.ndarray,
    tol: float,
) -> tuple[LevelKind, bool]:
    """Map origin + break history to current support/resistance role."""
    if origin == "high":
        broken_up = _sustained_break(closes, price, tol, upward=True)
        if broken_up and close_now >= price - tol:
            return LevelKind.SUPPORT, True
        return LevelKind.RESISTANCE, False
    broken_down = _sustained_break(closes, price, tol, upward=False)
    if broken_down and close_now <= price + tol:
        return LevelKind.RESISTANCE, True
    return LevelKind.SUPPORT, False


def _cluster_pivots(
    pivot_prices: np.ndarray,
    pivot_indices: np.ndarray,
    timestamps: pd.DatetimeIndex,
    tolerance: float,
    total_bars: int,
    origin: str,
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
                "origin": origin,
                "source": "swing",
            })
    return clusters


def _round_number_bonus(price: float) -> float:
    """Extra score when price sits on a traded round number."""
    if price >= 500:
        step = 10.0
    elif price >= 100:
        step = 5.0
    elif price >= 20:
        step = 1.0
    else:
        step = 0.5
    nearest = round(price / step) * step
    if nearest <= 0:
        return 0.0
    if abs(price - nearest) / nearest <= 0.002:
        return 8.0
    if abs(price - nearest) / nearest <= 0.005:
        return 4.0
    return 0.0


def _score_cluster(c: dict, sliced_len: int) -> float:
    t = min(c.get("retests", 0), 12)
    touch_pts = min(40, max(0, (t - 1) * 8))
    last_rel = (c.get("last_touch_idx") or 0) / max(1, sliced_len - 1)
    recency_pts = 25 * (last_rel ** 0.5)
    weight_pts = min(15, c.get("weight", 0.5) * 4)
    pivot_pts = min(10, max(0, (c.get("pivots", 1) - 1) * 4))
    vol_pts = min(15, c.get("volume_score", 0) * 0.15)
    bounce = c.get("bounce_rate")
    bounce_pts = 0.0
    if bounce is not None:
        bounce_pts = min(15, max(0, (bounce - 40) * 0.25))
    bonus = source_bonus(c.get("source", "swing"))
    bonus += _round_number_bonus(c.get("price", 0.0))
    flip_penalty = -5 if c.get("flipped") else 0
    return touch_pts + recency_pts + weight_pts + pivot_pts + vol_pts + bounce_pts + bonus + flip_penalty


def _source_rank(source: str) -> int:
    if source == "swing":
        return 4
    if source.startswith("volume"):
        return 3
    if source == "trendline":
        return 2
    if source.startswith("fib_"):
        return 1
    return 0


def _merge_candidates(candidates: list[dict], tol: float, sliced_len: int) -> list[dict]:
    merged: list[dict] = []
    for c in sorted(candidates, key=lambda x: x["price"]):
        placed = False
        for m in merged:
            if abs(c["price"] - m["price"]) <= tol:
                if _score_cluster(c, sliced_len) >= _score_cluster(m, sliced_len):
                    m.update({k: v for k, v in c.items() if k != "price"})
                    m["price"] = (m["price"] + c["price"]) / 2
                    m["pivots"] = m.get("pivots", 1) + c.get("pivots", 1)
                placed = True
                break
        if not placed:
            merged.append(dict(c))
    return merged


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
    closes = sliced["close"].to_numpy(dtype=float)

    if "atr" in sliced.columns and not np.isnan(sliced["atr"].iloc[-1]):
        atr_now = float(sliced["atr"].iloc[-1])
    else:
        atr_now = close_now * 0.005

    is_high, is_low = _swing_pivots(highs, lows, window)
    tol = cluster_atr_mult * atr_now
    timestamps = sliced.index

    candidates: list[dict] = []
    if is_high.any():
        candidates.extend(_cluster_pivots(
            highs[is_high], np.where(is_high)[0], timestamps, tol, len(sliced), "high",
        ))
    if is_low.any():
        candidates.extend(_cluster_pivots(
            lows[is_low], np.where(is_low)[0], timestamps, tol, len(sliced), "low",
        ))

    candidates.extend(trendline_candidates(
        highs, lows, is_high, is_low, timestamps, close_now,
    ))

    for node in volume_profile_nodes(sliced):
        origin = "high" if node["price"] > close_now else "low"
        candidates.append({
            "price": node["price"],
            "origin": origin,
            "source": node["source"],
            "pivots": 1,
            "weight": 0.5 + node.get("volume_share", 0.1),
            "last_touch_idx": len(sliced) - 1,
            "last_touch_ts": sliced.index[-1],
        })

    candidates.extend(fibonacci_candidates(sliced, close_now, is_high, is_low))

    price_range = float(np.max(highs) - np.min(lows))
    _ = price_range  # reserved for future range-aware filters

    for c in candidates:
        origin = c.get("origin", "high")
        stats = _retest_stats(sliced, c["price"], tol, origin)
        c.update(stats)
        c["hit_rate"] = walkforward_hit_rate(sliced, c["price"], tol, origin)
        kind, flipped = _assign_kind(origin, c["price"], close_now, closes, tol)
        c["kind"] = kind
        c["flipped"] = flipped

    candidates = _merge_candidates(candidates, tol, len(sliced))
    row = sliced.iloc[-1]

    def _eligible(c: dict) -> bool:
        src = c.get("source", "")
        if src.startswith("fib_"):
            return c.get("retests", 0) >= 2 and abs(c["price"] - close_now) / max(close_now, 1e-9) < 0.10
        if c.get("source") == "trendline":
            return c.get("pivots", 0) >= 2
        return c.get("pivots", 0) >= min_pivots and c.get("retests", 0) >= min_touches

    resistances = [c for c in candidates if c.get("kind") is LevelKind.RESISTANCE and c["price"] > close_now and _eligible(c)]
    supports = [c for c in candidates if c.get("kind") is LevelKind.SUPPORT and c["price"] < close_now and _eligible(c)]

    def _pick_top(pool: list[dict]) -> list[dict]:
        primary = [c for c in pool if not str(c.get("source", "")).startswith("fib_")]
        fib = [c for c in pool if str(c.get("source", "")).startswith("fib_")]
        primary.sort(
            key=lambda c: (_score_cluster(c, len(sliced)), _source_rank(c.get("source", ""))),
            reverse=True,
        )
        fib.sort(key=lambda c: _score_cluster(c, len(sliced)), reverse=True)
        picked = primary[:top_n]
        if len(picked) < top_n and fib:
            picked.append(fib[0])
        return picked[:top_n]

    resistances = _pick_top(resistances)
    supports = _pick_top(supports)

    levels: list[Level] = []
    for c in resistances:
        ma_al = ma_confluence(c["price"], row, atr_now)
        sc = calibrate_strength(
            _score_cluster(c, len(sliced)),
            bounce_rate=c.get("bounce_rate"),
            hit_rate=c.get("hit_rate"),
            ma_aligned=ma_al,
        )
        levels.append(Level(
            price=round(c["price"], 2),
            kind=LevelKind.RESISTANCE,
            touches=c.get("retests", 0),
            pivots=c.get("pivots", 1),
            strength=round(sc, 1),
            last_touch=c["last_touch_ts"],
            distance_pct=round((c["price"] / close_now - 1.0) * 100.0, 2),
            source=c.get("source", "swing"),
            origin=c.get("origin", "high"),
            flipped=bool(c.get("flipped")),
            bounce_rate=c.get("bounce_rate"),
            volume_score=round(c.get("volume_score", 0), 1),
            hit_rate=c.get("hit_rate"),
            ma_aligned=ma_al,
        ))
    for c in supports:
        ma_al = ma_confluence(c["price"], row, atr_now)
        sc = calibrate_strength(
            _score_cluster(c, len(sliced)),
            bounce_rate=c.get("bounce_rate"),
            hit_rate=c.get("hit_rate"),
            ma_aligned=ma_al,
        )
        levels.append(Level(
            price=round(c["price"], 2),
            kind=LevelKind.SUPPORT,
            touches=c.get("retests", 0),
            pivots=c.get("pivots", 1),
            strength=round(sc, 1),
            last_touch=c["last_touch_ts"],
            distance_pct=round((c["price"] / close_now - 1.0) * 100.0, 2),
            source=c.get("source", "swing"),
            origin=c.get("origin", "high"),
            flipped=bool(c.get("flipped")),
            bounce_rate=c.get("bounce_rate"),
            volume_score=round(c.get("volume_score", 0), 1),
            hit_rate=c.get("hit_rate"),
            ma_aligned=ma_al,
        ))
    levels.sort(key=lambda lv: (lv.kind.value, -lv.strength, abs(lv.distance_pct)))
    return levels


def structure_slice(
    df: pd.DataFrame,
    *,
    window: int | None = None,
    lookback_bars: int | None = None,
    trade_freq: str | None = None,
    daily_df: pd.DataFrame | None = None,
    reference_close: float | None = None,
) -> tuple[pd.DataFrame, float, int, float] | None:
    """Return (sliced OHLCV, close_now, pivot_window, atr_now) for structure analysis."""

    if df.empty or len(df) < 6:
        return None

    close_now = float(reference_close if reference_close is not None else df["close"].iloc[-1])
    bar_seconds = _median_bar_seconds(df.index)
    atr_now = float(df["atr"].iloc[-1]) if "atr" in df.columns and not np.isnan(df["atr"].iloc[-1]) else close_now * 0.005
    atr_ratio = atr_now / max(close_now, 1e-9)
    win = window if window is not None else _adaptive_window(atr_ratio)

    source = df
    source_lookback = lookback_bars
    if (
        daily_df is not None
        and not daily_df.empty
        and len(daily_df) >= win * 2 + 2
        and _is_sub_daily(trade_freq, bar_seconds)
    ):
        source = daily_df
        source_lookback = lookback_bars if lookback_bars is not None else _LOOKBACK_TARGET["1D"]
    elif lookback_bars is None:
        source_lookback = lookback_bars_for_freq(trade_freq, len(df))

    if source_lookback is None:
        source_lookback = 250
    sliced = source.tail(min(source_lookback, len(source))).copy()
    if len(sliced) < win * 2 + 2:
        return None
    return sliced, close_now, win, atr_now


def compute_levels(
    df: pd.DataFrame,
    *,
    window: int | None = None,
    cluster_atr_mult: float = 0.5,
    top_n: int = 4,
    min_touches: int = 2,
    min_pivots: int = 2,
    lookback_bars: int | None = None,
    trade_freq: str | None = None,
    daily_df: pd.DataFrame | None = None,
    reference_close: float | None = None,
) -> list[Level]:
    ctx = structure_slice(
        df,
        window=window,
        lookback_bars=lookback_bars,
        trade_freq=trade_freq,
        daily_df=daily_df,
        reference_close=reference_close,
    )
    if ctx is None:
        return []
    sliced, close_now, win, _ = ctx

    return _levels_from_slice(
        sliced,
        close_now,
        window=win,
        cluster_atr_mult=cluster_atr_mult,
        top_n=top_n,
        min_touches=min_touches,
        min_pivots=min_pivots,
    )
