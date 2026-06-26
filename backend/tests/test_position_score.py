"""Tests for position sub-score."""

from __future__ import annotations

import pandas as pd

from app.core.levels import Level, LevelKind
from app.core.signal.subscores import position_score


def test_position_score_neutral_without_levels() -> None:
    df = pd.DataFrame([{"close": 100.0}])
    assert position_score(df, []) == 50.0


def test_position_score_favors_near_support() -> None:
    df = pd.DataFrame([{"close": 100.0}])
    levels = [
        Level(
            price=99.0,
            kind=LevelKind.SUPPORT,
            touches=4,
            pivots=2,
            strength=80.0,
            last_touch=pd.Timestamp("2026-06-20"),
            distance_pct=-1.0,
        ),
    ]
    assert position_score(df, levels) > 50.0


def test_position_score_penalizes_near_resistance() -> None:
    df = pd.DataFrame([{"close": 100.0}])
    levels = [
        Level(
            price=101.0,
            kind=LevelKind.RESISTANCE,
            touches=4,
            pivots=2,
            strength=80.0,
            last_touch=pd.Timestamp("2026-06-20"),
            distance_pct=1.0,
        ),
    ]
    assert position_score(df, levels) < 50.0
