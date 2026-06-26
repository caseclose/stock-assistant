"""Volume indicators: OBV and VWAP."""

from __future__ import annotations

import numpy as np
import pandas as pd
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice


def compute_volume(df: pd.DataFrame, vwap_window: int = 14, obv_slope_window: int = 10) -> pd.DataFrame:
    """Add OBV, OBV slope (z-score over `obv_slope_window`), and rolling VWAP."""

    out = df.copy()
    out["obv"] = OnBalanceVolumeIndicator(
        close=df["close"], volume=df["volume"]
    ).on_balance_volume()
    out["vwap"] = VolumeWeightedAveragePrice(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"],
        window=vwap_window,
    ).volume_weighted_average_price()

    # OBV slope (per bar) over a rolling window, then z-scored against its own
    # 50-bar history. Captures whether accumulation is accelerating.
    def _slope(arr: np.ndarray) -> float:
        if np.isnan(arr).any() or len(arr) < 2:
            return np.nan
        x = np.arange(len(arr))
        return float(np.polyfit(x, arr, 1)[0])

    obv_slope = out["obv"].rolling(obv_slope_window).apply(_slope, raw=True)
    rolling_std = obv_slope.rolling(50, min_periods=10).std()
    rolling_mean = obv_slope.rolling(50, min_periods=10).mean()
    out["obv_slope_z"] = ((obv_slope - rolling_mean) / rolling_std).fillna(0.0)
    return out
