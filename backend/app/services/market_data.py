"""Market data orchestration."""

from __future__ import annotations

import pandas as pd

from app.core.data import fetch_warmup_bars, fetch_watchlist_quotes
from app.core.indicators import compute_all

VALID_INTERVALS = ("1Min", "5Min", "15Min", "1H", "1D")


class MarketDataService:
    def fetch_bars(
        self,
        symbol: str,
        interval: str = "1H",
        limit: int = 500,
        *,
        extended_hours: bool = True,
        before: int | None = None,
    ) -> tuple[pd.DataFrame, bool]:
        if interval not in VALID_INTERVALS:
            raise ValueError(f"invalid interval {interval}")
        before_ts = None
        if before is not None:
            before_ts = pd.Timestamp(before, unit="s", tz="UTC")
        raw = fetch_warmup_bars(
            symbol,
            interval,
            limit=limit,
            regular_hours_only=not extended_hours,
            before=before_ts,
        )
        if raw.empty:
            return raw, False
        if before_ts is not None:
            has_more = len(raw) >= limit
        else:
            # Initial load: allow pagination until a `before` request returns empty.
            has_more = len(raw) > 0
        return compute_all(raw), has_more

    def fetch_daily_enriched(self, symbol: str, limit: int = 400) -> pd.DataFrame:
        raw = fetch_warmup_bars(symbol, "1D", limit=limit, regular_hours_only=False)
        return compute_all(raw)

    def quotes_for_symbols(self, symbols: list[str]) -> dict:
        quotes = fetch_watchlist_quotes(tuple(symbols))
        return {
            sym: {
                "symbol": q.symbol,
                "price": q.price,
                "change_pct": round(q.change_pct, 2),
                "market_state": q.market_state,
            }
            for sym, q in quotes.items()
        }

    def bars_to_records(self, df: pd.DataFrame) -> list[dict]:
        records = []
        for ts, row in df.iterrows():
            rec = {
                "time": int(pd.Timestamp(ts).timestamp()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for col in df.columns:
                if col in ("open", "high", "low", "close", "volume"):
                    continue
                val = row[col]
                if pd.notna(val):
                    rec[col] = float(val)
            records.append(rec)
        return records
