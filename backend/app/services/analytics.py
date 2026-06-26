"""Analytics: indicators, levels, composite signal."""

from __future__ import annotations

from app.core.explain import (
    explain_level,
    explain_verdict,
    moving_average_snapshot,
)
from app.core.levels import compute_levels
from app.core.signal import compute_score

from .market_data import MarketDataService


class AnalyticsService:
    def __init__(self, market: MarketDataService) -> None:
        self.market = market

    def analyze(self, symbol: str, interval: str) -> dict:
        enriched = self.market.fetch_bars(symbol, interval)
        daily_df = None
        daily_sourced = False
        if interval != "1D":
            try:
                daily_df = self.market.fetch_daily_enriched(symbol)
                daily_sourced = True
            except Exception:
                daily_df = None
        score = compute_score(enriched)
        levels = compute_levels(
            enriched,
            trade_freq=interval,
            daily_df=daily_df,
        )
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
                    "reason_zh": le.reason_zh,
                    "reason_en": le.reason_en,
                }
                for le in level_items
            ],
            "moving_averages": moving_average_snapshot(enriched),
            "components": {k: round(v, 1) for k, v in score.components.items()},
        }
