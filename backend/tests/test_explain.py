"""Tests for explain templates."""

from __future__ import annotations

import pandas as pd

from app.core.explain import explain_level, explain_verdict, moving_average_snapshot
from app.core.levels import Level, LevelKind
from app.core.signal import ScoreBreakdown, Verdict


def _sample_row() -> pd.Series:
    return pd.Series({
        "close": 100.0,
        "ema20": 101.0,
        "ema50": 99.0,
        "rsi": 56.0,
        "sma20": 98.5,
    })


def test_explain_verdict_has_reasons() -> None:
    score = ScoreBreakdown(
        composite=52.0,
        verdict=Verdict.HOLD,
        components={"trend": 48.0, "momentum": 55.0, "bollinger": 50.0, "volume": 52.0, "vol_regime": 50.0, "position": 50.0},
    )
    df = pd.DataFrame([_sample_row()])
    zh, en, reasons = explain_verdict(score, df)
    assert "观望" in zh or "Hold" in en
    assert len(reasons) == 6
    assert all(r.text_zh and r.text_en for r in reasons)


def test_explain_level_templates() -> None:
    lv = Level(
        price=198.5,
        kind=LevelKind.RESISTANCE,
        strength=72.0,
        touches=5,
        pivots=3,
        distance_pct=2.1,
        last_touch=pd.Timestamp("2026-05-12"),
    )
    ex = explain_level(lv, daily_sourced=True)
    assert ex.kind == "resistance"
    assert "198.5" in ex.reason_zh
    assert "5" in ex.reason_zh


def test_moving_average_snapshot() -> None:
    df = pd.DataFrame([{
        "close": 100.0,
        "sma20": 95.0,
        "ema20": 98.0,
    }])
    mas = moving_average_snapshot(df)
    names = {m["name"] for m in mas}
    assert "SMA20" in names
    assert "EMA20" in names
