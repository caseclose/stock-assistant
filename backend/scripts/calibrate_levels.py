#!/usr/bin/env python3
"""Batch-calibrate S/R source weights from liquid US tickers (daily structure)."""

from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.data import fetch_warmup_bars  # noqa: E402
from app.core.indicators import compute_all  # noqa: E402
from app.core.level_backtest import save_calibration, walkforward_hit_rate  # noqa: E402
from app.core.levels import compute_levels, structure_slice  # noqa: E402

SYMBOLS = (
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "SPY", "QQQ",
    "JPM", "V", "UNH", "XOM", "AMD", "NFLX",
)


def _collect_symbol(symbol: str) -> dict[str, list[float]]:
    raw = fetch_warmup_bars(symbol, "1D", limit=400, regular_hours_only=False)
    if raw.empty or len(raw) < 80:
        return {}
    enriched = compute_all(raw)
    ctx = structure_slice(enriched, trade_freq="1D")
    if ctx is None:
        return {}
    sliced, close_now, win, atr = ctx
    tol = 0.5 * atr
    by_source: dict[str, list[float]] = defaultdict(list)
    for lv in compute_levels(enriched, trade_freq="1D"):
        rate = walkforward_hit_rate(sliced, lv.price, tol, lv.origin)
        if rate is not None:
            by_source[lv.source].append(rate)
    return by_source


def main() -> None:
    pooled: dict[str, list[float]] = defaultdict(list)
    ok = 0
    for sym in SYMBOLS:
        try:
            rates = _collect_symbol(sym)
            if rates:
                ok += 1
                for src, vals in rates.items():
                    pooled[src].extend(vals)
            print(f"{sym}: {sum(len(v) for v in rates.values())} samples")
        except Exception as exc:
            print(f"{sym}: skip ({exc})")

    if ok < 3:
        print("Too few symbols; calibration aborted.")
        sys.exit(1)

    medians = {src: round(statistics.median(vals), 1) for src, vals in pooled.items() if vals}
    base_bonus = {
        "swing": 12, "volume_poc": 10, "volume_vah": 6, "volume_val": 6,
        "trendline": 8, "fib_236": 5, "fib_382": 7, "fib_500": 8, "fib_618": 10, "fib_786": 6,
    }
    swing_med = medians.get("swing", 55.0)
    tuned = {}
    for src, med in medians.items():
        rel = med / max(swing_med, 1.0)
        tuned[src] = max(3, min(18, round(base_bonus.get(src, 6) * rel)))

    overall = [v for vals in pooled.values() for v in vals]
    hit_med = statistics.median(overall) if overall else 55.0
    blend_hit = 0.35 if hit_med < 50 else 0.45 if hit_med < 60 else 0.50

    payload = {
        "blend_bounce": 0.25,
        "blend_hit_rate": round(blend_hit, 2),
        "blend_heuristic_with_hit": round(1.0 - blend_hit * 0.85, 2),
        "ma_bonus_per": 4.0,
        "ma_bonus_cap": 12.0,
        "source_bonus": {**base_bonus, **tuned},
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
        "sample_symbols": list(SYMBOLS),
        "source_hit_rates": medians,
    }
    save_calibration(payload)
    print(f"Calibrated on {ok} symbols, median hold {hit_med:.1f}%")
    print(f"Wrote {ROOT / 'app/core/level_calibration.json'}")


if __name__ == "__main__":
    main()
