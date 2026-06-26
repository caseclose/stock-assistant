"""Tests for RTH bar filtering."""

from __future__ import annotations

import pandas as pd

from app.core.rth import filter_regular_hours, is_regular_hours_bar, rth_open_minutes


def test_hourly_bars_use_900_open() -> None:
    assert rth_open_minutes(60) == 540


def test_minute_bars_use_930_open() -> None:
    assert rth_open_minutes(5) == 570


def test_is_regular_hours_hourly_bar_at_900() -> None:
    ts = pd.Timestamp("2026-06-24 13:00:00", tz="UTC")  # 09:00 NY (EDT)
    assert is_regular_hours_bar(ts, gap_min=60) is True


def test_filter_regular_hours_drops_premarket_minute_bars() -> None:
    idx = pd.to_datetime(
        ["2026-06-24 13:00:00", "2026-06-24 13:30:00", "2026-06-24 14:00:00"],
        utc=True,
    )
    df = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=idx)
    out = filter_regular_hours(df)
    assert len(out) == 2
