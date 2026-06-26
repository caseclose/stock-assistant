"""Shared regular-trading-hours bar filter (REST + live stream)."""

from __future__ import annotations

import pandas as pd


def bar_gap_minutes(index: pd.DatetimeIndex) -> float:
    if len(index) < 2:
        return 60.0
    return float((index[-1] - index[-2]).total_seconds() / 60.0)


def rth_open_minutes(gap_min: float) -> int:
    """09:00 NY for hourly+ bars; 09:30 for sub-hour (matches Alpaca 1H bar opens)."""
    return 540 if gap_min >= 60 else 570


def is_regular_hours_bar(ts: pd.Timestamp, *, gap_min: float = 60.0) -> bool:
    if ts.tz is None:
        ts_ny = ts.tz_localize("UTC").tz_convert("America/New_York")
    else:
        ts_ny = ts.tz_convert("America/New_York")
    if ts_ny.weekday() >= 5:
        return False
    minutes = ts_ny.hour * 60 + ts_ny.minute
    lo = rth_open_minutes(gap_min)
    return lo <= minutes < 960


def filter_regular_hours(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    gap_min = bar_gap_minutes(df.index)
    lo = rth_open_minutes(gap_min)
    idx = df.index
    ts_ny = idx.tz_localize("UTC").tz_convert("America/New_York") if idx.tz is None else idx.tz_convert("America/New_York")
    minutes = ts_ny.hour * 60 + ts_ny.minute
    mask = (minutes >= lo) & (minutes < 960) & (ts_ny.weekday < 5)
    return df.loc[mask]
