"""Trend indicators: EMA, SMA, MACD."""

from __future__ import annotations

import pandas as pd
from ta.trend import EMAIndicator, MACD, SMAIndicator


def compute_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Add common moving averages plus MACD."""

    close = df["close"]
    out = df.copy()
    for w in (5, 10, 20, 60, 120, 200):
        out[f"sma{w}"] = SMAIndicator(close=close, window=w).sma_indicator()
    out["ema20"] = EMAIndicator(close=close, window=20).ema_indicator()
    out["ema50"] = EMAIndicator(close=close, window=50).ema_indicator()
    macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()
    return out
