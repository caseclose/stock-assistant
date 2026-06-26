"""Compute all indicators in one pass."""

from __future__ import annotations

import pandas as pd

from .momentum import compute_momentum
from .trend import compute_trend
from .volatility import compute_volatility
from .volume import compute_volume


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Apply trend, momentum, volatility, and volume indicators in sequence.

    Input must contain columns: ``open``, ``high``, ``low``, ``close``, ``volume``.
    Returned frame is the input plus indicator columns.
    """

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame missing columns: {sorted(missing)}")

    out = compute_trend(df)
    out = compute_momentum(out)
    out = compute_volatility(out)
    out = compute_volume(out)
    return out


__all__ = [
    "compute_all",
    "compute_trend",
    "compute_momentum",
    "compute_volatility",
    "compute_volume",
]
