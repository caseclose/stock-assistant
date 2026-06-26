"""Per-dimension sub-scores. Each maps an indicator state to 0-100 where 50 is
neutral, >50 leans bullish, and <50 leans bearish.

All scorers consume the indicator-enriched DataFrame produced by
``quant.indicators.compute_all`` and look at the **last row only** (signal is a
snapshot of "now"). Lookback windows for things like the OBV slope live inside
the indicator module.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if math.isnan(x) or math.isinf(x):
        return 50.0
    return max(lo, min(hi, x))


def trend_score(df: pd.DataFrame) -> float:
    """Trend = 60% MACD-histogram-vs-ATR + 40% EMA20 vs EMA50 separation."""

    row = df.iloc[-1]
    atr = row.get("atr", np.nan)
    macd_hist = row.get("macd_hist", 0.0)
    if atr is None or math.isnan(atr) or atr == 0:
        s_macd = 50.0
    else:
        s_macd = math.tanh(macd_hist / atr) * 50.0 + 50.0

    price = row["close"]
    ema20 = row.get("ema20", price)
    ema50 = row.get("ema50", price)
    if math.isnan(ema20) or math.isnan(ema50) or price == 0:
        s_ema = 50.0
    else:
        rel = (ema20 - ema50) / (0.02 * price)  # 2% separation -> full scale
        s_ema = 50.0 + 50.0 * max(-1.0, min(1.0, rel))

    return _clip(0.6 * s_macd + 0.4 * s_ema)


def momentum_score(df: pd.DataFrame) -> float:
    """RSI mapped piecewise:

    - RSI < 30 (oversold): score 30-45 (mild bullish reversal credit)
    - RSI 30-70 (normal):  linear map -> 45-75
    - RSI 70-85 (strong):  stays in 75-65 zone (strength is good but momentum
      can fade soon)
    - RSI > 85 (extreme):  drops 65 -> 45 as RSI -> 100 (overbought penalty,
      but never below 45 — don't flip momentum to bearish just because trend
      is strong)
    """

    rsi = df["rsi"].iloc[-1]
    if math.isnan(rsi):
        return 50.0
    if rsi < 30:
        s = 30.0 + (rsi / 30.0) * 15.0
    elif rsi <= 70:
        s = 45.0 + ((rsi - 30.0) / 40.0) * 30.0
    elif rsi <= 85:
        s = 75.0 - ((rsi - 70.0) / 15.0) * 10.0
    else:
        s = 65.0 - ((rsi - 85.0) / 15.0) * 20.0
    return _clip(s)


def bollinger_score(df: pd.DataFrame) -> float:
    """%B-based score: discount-to-lower-band -> bullish, near-upper -> mildly
    bearish (but a price that rides the upper band is showing strength, not
    weakness — we cap the downside at 35).
    """

    pct_b = df["bb_pct_b"].iloc[-1]
    if math.isnan(pct_b):
        return 50.0
    if pct_b < 0.2:
        s = 80.0 - 20.0 * (pct_b / 0.2)        # 80 at 0.0 -> 60 at 0.2
    elif pct_b <= 0.8:
        s = 60.0 - 20.0 * abs(pct_b - 0.4) / 0.4
    else:
        # 0.8 -> 50 (neutral; riding upper band can be bullish in strong trends)
        # 1.0 -> 40 (extended, mild caution)
        # >1.0 -> 35 (above upper band, real overextension)
        s = 50.0 - min(15.0, (pct_b - 0.8) * 50.0)
    return _clip(s)


def volume_score(df: pd.DataFrame) -> float:
    """OBV slope z-score (60%) + price-vs-VWAP deviation (40%)."""

    row = df.iloc[-1]
    obv_z = row.get("obv_slope_z", 0.0)
    if math.isnan(obv_z):
        obv_z = 0.0
    s_obv = 50.0 + 50.0 * math.tanh(obv_z)

    vwap = row.get("vwap", row["close"])
    if math.isnan(vwap) or vwap == 0:
        s_vwap = 50.0
    else:
        dev = (row["close"] - vwap) / vwap
        # 1% premium to VWAP -> +10 points; clamp at ±25.
        s_vwap = 50.0 + max(-25.0, min(25.0, dev * 1000.0))

    return _clip(0.6 * s_obv + 0.4 * s_vwap)


def position_score(df: pd.DataFrame, levels: list) -> float:
    """Proximity to strong S/R: near resistance → lower, near support → higher."""

    if not levels:
        return 50.0
    close = float(df["close"].iloc[-1])
    if close <= 0:
        return 50.0

    score = 50.0
    for lv in levels:
        dist_pct = abs(getattr(lv, "distance_pct", (lv.price / close - 1) * 100))
        proximity = max(0.0, 1.0 - dist_pct / 2.5)
        strength = getattr(lv, "strength", 50.0) / 100.0
        kind = getattr(lv, "kind", None)
        kind_val = kind.value if hasattr(kind, "value") else str(kind)
        if kind_val == "resistance":
            score -= proximity * strength * 28.0
        else:
            score += proximity * strength * 28.0
    return _clip(score)


def vol_regime_score(df: pd.DataFrame) -> float:
    """Low realized vol = mildly bullish (smoother trend can run);
    high vol = mildly bearish (chop / risk-off).

    Compares ATR/price to its own 20-bar rolling mean.
    """

    if len(df) < 20:
        return 50.0
    ratio = df["atr"] / df["close"]
    last = ratio.iloc[-1]
    mean20 = ratio.rolling(20).mean().iloc[-1]
    if math.isnan(last) or math.isnan(mean20) or mean20 == 0:
        return 50.0
    rel = last / mean20  # 1.0 = average, >1 = elevated vol
    s = 50.0 + (1.0 - rel) * 30.0
    return _clip(s)
