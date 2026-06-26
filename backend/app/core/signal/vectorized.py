"""Vectorized signal scoring — same math as ``quant.signal.subscores`` but
computed for every bar in one shot.

The dashboard hot path can keep using the row-by-row API in
``quant.signal.subscores`` (it's clearer and the cost is negligible for one
snapshot). The backtester loops millions of times and needs this version.

Returns a DataFrame with columns:
    trend, momentum, bollinger, volume, vol_regime, composite
indexed identically to the input. Pre-warmup rows where indicators are NaN
get a neutral 50.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .composite import WEIGHTS


def _tanh_clip(arr: np.ndarray) -> np.ndarray:
    return np.tanh(arr)


def _safe(series: pd.Series, fill: float = np.nan) -> np.ndarray:
    return series.to_numpy(dtype=float, copy=False, na_value=fill)


def vector_subscores(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-bar 0-100 sub-scores + composite."""

    close = _safe(df["close"], np.nan)
    atr = _safe(df["atr"], np.nan)
    macd_hist = _safe(df["macd_hist"], 0.0)
    ema20 = _safe(df["ema20"], np.nan)
    ema50 = _safe(df["ema50"], np.nan)
    rsi = _safe(df["rsi"], np.nan)
    pct_b = _safe(df["bb_pct_b"], np.nan)
    obv_z = _safe(df["obv_slope_z"], 0.0)
    vwap = _safe(df["vwap"], np.nan)

    # --- trend: 0.6 * macd-vs-atr + 0.4 * ema20/ema50 separation ---
    with np.errstate(divide="ignore", invalid="ignore"):
        s_macd = np.where(
            (atr > 0) & np.isfinite(atr),
            _tanh_clip(macd_hist / np.where(atr == 0, np.nan, atr)) * 50.0 + 50.0,
            50.0,
        )
        rel = np.where(close == 0, 0.0, (ema20 - ema50) / (0.02 * close))
        rel = np.clip(rel, -1.0, 1.0)
        s_ema = 50.0 + 50.0 * rel
        s_ema = np.where(np.isfinite(ema20) & np.isfinite(ema50), s_ema, 50.0)
    trend = np.clip(0.6 * s_macd + 0.4 * s_ema, 0.0, 100.0)

    # --- momentum: piecewise RSI ---
    mom = np.full_like(rsi, 50.0)
    mask = np.isfinite(rsi)
    r = np.where(mask, rsi, 50.0)
    mom = np.select(
        [r < 30, r <= 70, r <= 85, r > 85],
        [
            30.0 + (r / 30.0) * 15.0,
            45.0 + ((r - 30.0) / 40.0) * 30.0,
            75.0 - ((r - 70.0) / 15.0) * 10.0,
            65.0 - ((r - 85.0) / 15.0) * 20.0,
        ],
        default=50.0,
    )
    mom = np.where(mask, mom, 50.0)
    momentum = np.clip(mom, 0.0, 100.0)

    # --- bollinger %B ---
    pb = np.where(np.isfinite(pct_b), pct_b, 0.5)
    bb = np.select(
        [pb < 0.2, pb <= 0.8, pb > 0.8],
        [
            80.0 - 20.0 * (pb / 0.2),
            60.0 - 20.0 * np.abs(pb - 0.4) / 0.4,
            50.0 - np.minimum(15.0, (pb - 0.8) * 50.0),
        ],
        default=50.0,
    )
    bollinger = np.clip(bb, 0.0, 100.0)

    # --- volume: 0.6 * tanh(obv_z) + 0.4 * vwap deviation ---
    s_obv = 50.0 + 50.0 * np.tanh(np.nan_to_num(obv_z, nan=0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        dev = np.where((vwap > 0) & np.isfinite(vwap), (close - vwap) / vwap, 0.0)
    s_vwap = 50.0 + np.clip(dev * 1000.0, -25.0, 25.0)
    s_vwap = np.where(np.isfinite(vwap) & (vwap > 0), s_vwap, 50.0)
    volume = np.clip(0.6 * s_obv + 0.4 * s_vwap, 0.0, 100.0)

    # --- vol regime: ATR/price vs its own 20-bar rolling mean ---
    ratio = pd.Series(np.where(close > 0, atr / np.where(close == 0, np.nan, close), np.nan), index=df.index)
    mean20 = ratio.rolling(20, min_periods=5).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_vol = np.where(np.isfinite(mean20) & (mean20 > 0), ratio.to_numpy() / mean20, 1.0)
    vr = 50.0 + (1.0 - rel_vol) * 30.0
    vr = np.where(np.isfinite(rel_vol), vr, 50.0)
    vol_regime = np.clip(vr, 0.0, 100.0)

    return pd.DataFrame(
        {
            "trend": trend,
            "momentum": momentum,
            "bollinger": bollinger,
            "volume": volume,
            "vol_regime": vol_regime,
        },
        index=df.index,
    )


def vector_composite(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Per-bar composite + sub-scores. Weights default to ``signal.composite.WEIGHTS``."""

    w = weights or WEIGHTS
    sub = vector_subscores(df)
    composite = (
        sub["trend"] * w.get("trend", 0.0)
        + sub["momentum"] * w.get("momentum", 0.0)
        + sub["bollinger"] * w.get("bollinger", 0.0)
        + sub["volume"] * w.get("volume", 0.0)
        + sub["vol_regime"] * w.get("vol_regime", 0.0)
    )
    sub["composite"] = composite
    return sub
