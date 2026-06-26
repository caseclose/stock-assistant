"""Walk-forward hit-rate calibration for S/R levels."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

_CALIB_PATH = Path(__file__).with_name("level_calibration.json")

_DEFAULT_CALIB: dict = {
    "blend_bounce": 0.25,
    "blend_hit_rate": 0.45,
    "blend_heuristic_with_hit": 0.55,
    "ma_bonus_per": 4.0,
    "ma_bonus_cap": 12.0,
    "source_bonus": {
        "swing": 12,
        "volume_poc": 10,
        "volume_vah": 6,
        "volume_val": 6,
        "trendline": 8,
        "fib_236": 5,
        "fib_382": 7,
        "fib_500": 8,
        "fib_618": 10,
        "fib_786": 6,
    },
}


@lru_cache(maxsize=1)
def load_calibration() -> dict:
    try:
        data = json.loads(_CALIB_PATH.read_text(encoding="utf-8"))
        merged = dict(_DEFAULT_CALIB)
        merged.update({k: v for k, v in data.items() if k != "source_bonus"})
        merged["source_bonus"] = {**_DEFAULT_CALIB["source_bonus"], **data.get("source_bonus", {})}
        return merged
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULT_CALIB)


def save_calibration(data: dict) -> None:
    _CALIB_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    load_calibration.cache_clear()


def walkforward_hit_rate(
    sliced: pd.DataFrame,
    price: float,
    tol: float,
    origin: str,
    *,
    forward_bars: int = 5,
    holdout_tail: int = 8,
) -> float | None:
    if len(sliced) < forward_bars + holdout_tail + 5:
        return None

    highs = sliced["high"].to_numpy(dtype=float)
    lows = sliced["low"].to_numpy(dtype=float)
    closes = sliced["close"].to_numpy(dtype=float)
    band_lo, band_hi = price - tol, price + tol
    touch_mask = (lows <= band_hi) & (highs >= band_lo)

    end = len(sliced) - holdout_tail
    holds = 0
    breaks = 0
    for i in np.where(touch_mask)[0]:
        if i >= end - forward_bars:
            continue
        fwd = closes[i + 1:i + 1 + forward_bars]
        if len(fwd) < forward_bars:
            continue
        if origin == "high":
            if np.any(fwd > price + tol):
                breaks += 1
            elif np.any(fwd < price - tol):
                holds += 1
        else:
            if np.any(fwd < price - tol):
                breaks += 1
            elif np.any(fwd > price + tol):
                holds += 1

    total = holds + breaks
    if total < 2:
        return None
    return round(100.0 * holds / total, 1)


def source_bonus(source: str) -> float:
    return float(load_calibration()["source_bonus"].get(source, 0))


def calibrate_strength(
    base: float,
    *,
    bounce_rate: float | None,
    hit_rate: float | None,
    ma_aligned: list[str],
) -> float:
    cfg = load_calibration()
    score = base
    if bounce_rate is not None:
        w = float(cfg["blend_bounce"])
        score = (1.0 - w) * score + w * bounce_rate
    if hit_rate is not None:
        w = float(cfg["blend_hit_rate"])
        h = float(cfg["blend_heuristic_with_hit"])
        score = h * score + w * hit_rate
    score += min(float(cfg["ma_bonus_cap"]), len(ma_aligned) * float(cfg["ma_bonus_per"]))
    return min(100.0, max(0.0, score))
