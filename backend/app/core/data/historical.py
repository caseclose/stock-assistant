"""Historical bar fetch via Alpaca REST."""

from __future__ import annotations

import pandas as pd
from alpaca.common.enums import Sort
from alpaca.data.enums import Adjustment
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from app.core.config import get_settings

# Minimum bars required for our indicators to settle:
# - EMA50 needs 50 bars
# - ATR14 / RSI14 need 14+
# - Bollinger 20 / OBV slope window 50
# 60 is a safe minimum; below this we refuse to compute and tell the user.
MIN_BARS_FOR_INDICATORS = 60

# Map UI labels to Alpaca TimeFrame objects.
TIMEFRAMES: dict[str, TimeFrame] = {
    "1Min": TimeFrame(1, TimeFrameUnit.Minute),
    "5Min": TimeFrame(5, TimeFrameUnit.Minute),
    "15Min": TimeFrame(15, TimeFrameUnit.Minute),
    "1H": TimeFrame(1, TimeFrameUnit.Hour),
    "1D": TimeFrame(1, TimeFrameUnit.Day),
}


def _filter_regular_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only bars whose timestamp falls in the regular trading session.

    Alpaca returns bar timestamps as the bar's *open* moment in UTC. For
    intraday bars >= 1h we keep 09:00–16:00 NY time (the 09:00 bar
    aggregates 09:00–10:00 which spans the 09:30 official open). For
    sub-hour bars we use the strict 09:30–16:00 window.
    """

    if df.empty:
        return df
    idx = df.index
    ts_ny = idx.tz_localize("UTC").tz_convert("America/New_York") if idx.tz is None else idx.tz_convert("America/New_York")
    minutes = ts_ny.hour * 60 + ts_ny.minute
    # Detect bar size by the gap between the two most recent rows.
    if len(df) >= 2:
        gap_min = (idx[-1] - idx[-2]).total_seconds() / 60
    else:
        gap_min = 60
    lo = 540 if gap_min >= 60 else 570  # 09:00 for hourly+, 09:30 otherwise
    mask = (minutes >= lo) & (minutes < 960) & (ts_ny.weekday < 5)
    return df.loc[mask]


def fetch_warmup_bars(
    symbol: str,
    timeframe_label: str = "1H",
    limit: int = 200,
    regular_hours_only: bool = True,
) -> pd.DataFrame:
    """Fetch ``limit`` historical bars for indicator warm-up.

    Returns a DataFrame indexed by timestamp with columns
    ``open / high / low / close / volume``.

    ``regular_hours_only``: when True (the default), drop pre-market /
    after-hours bars so indicators aren't polluted by thin liquidity.
    Daily bars are unaffected.
    """

    settings = get_settings()
    if not settings.has_credentials:
        raise RuntimeError(
            "Alpaca API credentials missing — set ALPACA_API_KEY and "
            "ALPACA_SECRET_KEY in your .env file."
        )

    tf = TIMEFRAMES.get(timeframe_label)
    if tf is None:
        raise ValueError(f"Unknown timeframe {timeframe_label!r}; choose from {list(TIMEFRAMES)}")

    client = StockHistoricalDataClient(settings.alpaca_api_key, settings.alpaca_secret_key)
    # Alpaca's bar endpoint pages forward from `start`. Two gotchas to avoid:
    #
    # 1. `StockBarsRequest.limit` is the TOTAL row cap across all pages, not a
    #    page size. Combined with default ascending sort, a too-small `limit`
    #    truncates at the OLD end of the window and we never reach "now". For
    #    intraday timeframes (1Min / 5Min) the window easily holds 1000+ bars,
    #    so we sort DESC and pull up to the API's hard cap (10_000) — the most
    #    recent bars are then guaranteed to be in the response.
    # 2. The free Alpaca tier rejects queries within ~15 minutes of "now"
    #    ("subscription does not permit querying recent SIP data"), so we
    #    subtract a 16-minute cushion from `end`. pd.Timestamp.utcnow() is
    #    deprecated in pandas 2.1+, use Timestamp.now(tz=UTC) instead.
    now = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=16)
    if timeframe_label == "1D":
        # Calendar days back ~= trading days * 1.5 (weekends + holidays).
        days_back = max(365, int(limit * 1.5))
        fetch_limit = limit * 2  # daily windows are small; no truncation risk
    elif regular_hours_only:
        days_back_per_bar = {"1H": 1 / 6, "15Min": 1 / 26, "5Min": 1 / 78, "1Min": 1 / 390}.get(timeframe_label, 1 / 6)
        days_back = max(3, int(limit * days_back_per_bar * 2))
        fetch_limit = 10000  # API hard cap — newest-first ensures we get "now"
    else:
        days_back_per_bar = {"1H": 1 / 24, "15Min": 1 / 96, "5Min": 1 / 288, "1Min": 1 / 1440}.get(timeframe_label, 1 / 24)
        days_back = max(3, int(limit * days_back_per_bar * 1.5))
        fetch_limit = 10000
    start = now - pd.Timedelta(days=days_back)
    req = StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=tf,
        start=start, end=now, limit=fetch_limit,
        adjustment=Adjustment.ALL,
        # DESC = newest first; combined with the 10k cap above, we always
        # capture the most recent bars even when the window holds far more
        # than `limit`. The DataFrame is sorted ascending again below.
        sort=Sort.DESC,
    )
    bars = client.get_stock_bars(req).df
    if bars.empty:
        raise RuntimeError(
            f"No bars returned for {symbol}. Check the ticker spelling and "
            f"that it's a US equity tradable on Alpaca."
        )
    bars = bars.reset_index(level=0, drop=True)
    bars = bars[["open", "high", "low", "close", "volume"]]
    # DESC fetch returns newest-first; restore chronological order for
    # downstream indicators (which assume df is sorted ascending).
    bars = bars.sort_index()
    if regular_hours_only and timeframe_label != "1D":
        bars = _filter_regular_hours(bars)
    bars = bars.tail(limit)
    if len(bars) < MIN_BARS_FOR_INDICATORS:
        raise RuntimeError(
            f"Only {len(bars)} bars available for {symbol} ({timeframe_label}); "
            f"need at least {MIN_BARS_FOR_INDICATORS} for indicators to settle. "
            "This usually means the ticker is newly listed, recently spun off, "
            "or delisted. Try a more liquid ticker like AAPL, SPY, or QQQ."
        )
    return bars
