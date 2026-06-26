"""Momentum indicators: RSI."""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator


def compute_momentum(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Add RSI column."""

    out = df.copy()
    out["rsi"] = RSIIndicator(close=df["close"], window=window).rsi()
    return out
