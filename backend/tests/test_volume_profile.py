"""Tests for volume profile nodes."""

from __future__ import annotations

import pandas as pd

from app.core.volume_profile import volume_profile_nodes


def test_volume_profile_finds_poc() -> None:
    n = 60
    prices = [100.0 + (i % 10) for i in range(n)]
    df = pd.DataFrame({
        "high": [p + 0.5 for p in prices],
        "low": [p - 0.5 for p in prices],
        "close": prices,
        "volume": [1_000_000 if p > 104 else 100_000 for p in prices],
    }, index=pd.bdate_range(end="2026-06-22", periods=n, freq="B"))
    nodes = volume_profile_nodes(df)
    assert nodes
    poc = next(n for n in nodes if n["source"] == "volume_poc")
    assert 104 <= poc["price"] <= 106
