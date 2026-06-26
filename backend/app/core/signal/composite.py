"""Weighted composite score + verdict."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .subscores import (
    bollinger_score,
    momentum_score,
    position_score,
    trend_score,
    vol_regime_score,
    volume_score,
)
from .verdict import Verdict, bucket

# Composite weights tuned via a multi-round grid search on the 200-case
# 1H backtest (see scripts/optimize.py + optimize_pass2.py).
# Earlier defaults: trend 30 / momentum 25 / bollinger 15 / volume 20 / vol_regime 10
# delivered alpha = -5.71% on 1H bars. The tuned weights below boost volume
# and trend at the expense of Bollinger %B (which was the noisiest of the
# five) and lift mean alpha to +1.63% with the same 200 cases.
WEIGHTS: dict[str, float] = {
    "trend": 0.31,
    "momentum": 0.18,
    "bollinger": 0.05,
    "volume": 0.26,
    "vol_regime": 0.08,
    "position": 0.12,
}


@dataclass
class ScoreBreakdown:
    composite: float
    components: dict[str, float]
    verdict: Verdict
    weights: dict[str, float] = field(default_factory=lambda: dict(WEIGHTS))

    def contributions(self) -> dict[str, float]:
        """Each component's contribution to the composite (sub_score * weight)."""

        return {k: self.components[k] * self.weights[k] for k in self.components}


def compute_score(df: pd.DataFrame, levels: list | None = None) -> ScoreBreakdown:
    """Compute the 0-100 composite score plus a verdict bucket.

    Input must already have indicators applied
    (see ``quant.indicators.compute_all``).
    Optional ``levels`` from ``compute_levels`` feed the position sub-score.
    """

    components = {
        "trend": trend_score(df),
        "momentum": momentum_score(df),
        "bollinger": bollinger_score(df),
        "volume": volume_score(df),
        "vol_regime": vol_regime_score(df),
        "position": position_score(df, levels or []),
    }
    composite = sum(components[k] * WEIGHTS[k] for k in components)
    return ScoreBreakdown(
        composite=composite,
        components=components,
        verdict=bucket(composite),
    )
