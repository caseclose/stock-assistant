"""Volatility indicators: Bollinger Bands and ATR."""

from __future__ import annotations

import numpy as np
import pandas as pd
from ta.volatility import AverageTrueRange, BollingerBands


def compute_volatility(df: pd.DataFrame, bb_window: int = 20, atr_window: int = 14) -> pd.DataFrame:
    """Add Bollinger Bands (upper / middle / lower / %B) and ATR columns."""

    out = df.copy()
    bb = BollingerBands(close=df["close"], window=bb_window, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_middle"] = bb.bollinger_mavg()
    out["bb_lower"] = bb.bollinger_lband()
    # %B = (close - lower) / (upper - lower); fall back to 0.5 when band is flat.
    band_width = (out["bb_upper"] - out["bb_lower"]).replace(0, np.nan)
    pct_b = (df["close"] - out["bb_lower"]) / band_width
    out["bb_pct_b"] = pct_b.fillna(0.5)

    out["atr"] = AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=atr_window
    ).average_true_range()
    return out
