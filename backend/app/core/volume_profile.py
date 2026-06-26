"""Fixed-range volume profile (POC / value area) for S/R anchoring."""

from __future__ import annotations

import numpy as np
import pandas as pd


def volume_profile_nodes(
    df: pd.DataFrame,
    *,
    bin_count: int = 48,
    value_area_pct: float = 0.70,
) -> list[dict]:
    """Return POC and value-area high/low from OHLCV.

    Uses typical price ``(H+L+C)/3`` weighted by volume. Returns up to three
    nodes with relative ``volume_share`` in ``(0, 1]``.
    """

    if df.empty or len(df) < 10 or "volume" not in df.columns:
        return []

    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)
    volumes = df["volume"].to_numpy(dtype=float)
    if volumes.sum() <= 0:
        return []

    typical = (highs + lows + closes) / 3.0
    lo, hi = float(np.min(lows)), float(np.max(highs))
    if hi <= lo:
        return []

    edges = np.linspace(lo, hi, bin_count + 1)
    centers = (edges[:-1] + edges[1:]) / 2.0
    hist = np.zeros(bin_count, dtype=float)
    for tp, vol in zip(typical, volumes):
        idx = int(np.clip(np.searchsorted(edges, tp, side="right") - 1, 0, bin_count - 1))
        hist[idx] += vol

    total = hist.sum()
    if total <= 0:
        return []

    poc_idx = int(np.argmax(hist))
    poc_price = float(centers[poc_idx])
    poc_share = float(hist[poc_idx] / total)

    order = np.argsort(hist)[::-1]
    covered = 0.0
    selected: list[int] = []
    target = total * value_area_pct
    for idx in order:
        selected.append(int(idx))
        covered += hist[idx]
        if covered >= target:
            break
    va_prices = centers[selected]
    vah = float(np.max(va_prices))
    val = float(np.min(va_prices))

    nodes: list[dict] = [
        {"price": poc_price, "source": "volume_poc", "volume_share": poc_share},
    ]
    if vah > poc_price + (hi - lo) * 0.002:
        nodes.append({"price": vah, "source": "volume_vah", "volume_share": poc_share * 0.85})
    if val < poc_price - (hi - lo) * 0.002:
        nodes.append({"price": val, "source": "volume_val", "volume_share": poc_share * 0.85})
    return nodes
