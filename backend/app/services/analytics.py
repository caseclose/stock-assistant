"""Analytics: indicators, levels, composite signal."""

from __future__ import annotations

import pandas as pd

from app.core.explain import (
    explain_level,
    explain_verdict,
    moving_average_snapshot,
)
from app.core.levels import compute_levels, structure_slice
from app.core.signal import compute_score
from app.core.trendlines import compute_trendline_segments

from .market_data import MarketDataService


class AnalyticsService:
    def __init__(self, market: MarketDataService) -> None:
        self.market = market

    def analyze(self, symbol: str, interval: str, *, extended_hours: bool = True) -> dict:
        enriched, _ = self.market.fetch_bars(symbol, interval, extended_hours=extended_hours)
        daily_df = None
        daily_sourced = False
        if interval != "1D":
            try:
                daily_df = self.market.fetch_daily_enriched(symbol)
                daily_sourced = True
            except Exception:
                daily_df = None
        levels = compute_levels(
            enriched,
            trade_freq=interval,
            daily_df=daily_df,
        )
        trendlines: list[dict] = []
        ctx = structure_slice(enriched, trade_freq=interval, daily_df=daily_df)
        if ctx is not None:
            sliced, close_now, win, _ = ctx
            t_end_chart = (
                int(pd.Timestamp(enriched.index[-1]).timestamp())
                if interval != "1D"
                else None
            )
            for tl in compute_trendline_segments(
                sliced, close_now, window=win, t_end_override=t_end_chart,
            ):
                trendlines.append({
                    "kind": tl.kind,
                    "t1": tl.t1,
                    "p1": tl.p1,
                    "t2": tl.t2,
                    "p2": tl.p2,
                    "t_end": tl.t_end,
                    "p_end": tl.p_end,
                    "strength": tl.strength,
                })
        score = compute_score(enriched, levels)
        summary_zh, summary_en, reasons = explain_verdict(score, enriched)
        level_items = [explain_level(lv, daily_sourced=daily_sourced) for lv in levels]
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "verdict": score.verdict.value,
            "composite": round(score.composite, 1),
            "summary_zh": summary_zh,
            "summary_en": summary_en,
            "verdict_reasons": [
                {
                    "key": r.key,
                    "score": r.score,
                    "weight": r.weight,
                    "text_zh": r.text_zh,
                    "text_en": r.text_en,
                }
                for r in reasons
            ],
            "levels": [
                {
                    "price": le.price,
                    "kind": le.kind,
                    "strength": le.strength,
                    "touches": le.touches,
                    "pivots": le.pivots,
                    "distance_pct": le.distance_pct,
                    "source": le.source,
                    "flipped": le.flipped,
                    "bounce_rate": le.bounce_rate,
                    "volume_score": le.volume_score,
                    "hit_rate": le.hit_rate,
                    "ma_aligned": le.ma_aligned,
                    "reason_zh": le.reason_zh,
                    "reason_en": le.reason_en,
                }
                for le in level_items
            ],
            "trendlines": trendlines,
            "moving_averages": moving_average_snapshot(enriched),
            "components": {k: round(v, 1) for k, v in score.components.items()},
        }
