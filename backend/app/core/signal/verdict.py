"""Verdict enum and bucket mapping for the composite score.

Buckets default to the *tuned* thresholds from the 200-case 1H backtest:

    < 30        STRONG_SELL
    [30, 44)    SELL
    [44, 58)    HOLD
    [58, 75)    BUY
    >= 75       STRONG_BUY

The tighter 44/58 entry/exit thresholds (vs 45/55 originally) raise the bar
for action and were worth ~+2% alpha in the grid search.
"""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    HOLD = "HOLD"
    BUY = "BUY"
    STRONG_BUY = "STRONG_BUY"


# Inclusive lower bound, exclusive upper bound — except STRONG_BUY which is closed.
DEFAULT_BUCKETS: tuple[tuple[float, float, Verdict], ...] = (
    (0.0, 30.0, Verdict.STRONG_SELL),
    (30.0, 44.0, Verdict.SELL),
    (44.0, 58.0, Verdict.HOLD),
    (58.0, 75.0, Verdict.BUY),
    (75.0, 100.01, Verdict.STRONG_BUY),
)


def bucket(score: float, buckets=DEFAULT_BUCKETS) -> Verdict:
    """Map a 0-100 composite score to a Verdict bucket.

    NaN / inf are treated as HOLD (we have no information).
    """

    import math
    fs = float(score)
    if math.isnan(fs) or math.isinf(fs):
        return Verdict.HOLD
    fs = max(0.0, min(100.0, fs))
    for lo, hi, v in buckets:
        if lo <= fs < hi:
            return v
    return Verdict.HOLD  # pragma: no cover — unreachable thanks to clamping
