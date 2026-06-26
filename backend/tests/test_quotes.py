"""Quote session labeling tests."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.core.data.quotes import (
    _refresh_with_bar_quote,
    resolve_snapshot_quote,
)
from app.core.data.yahoo import YahooQuote
from app.core.market import NY, MarketState, MarketStatus, session_label_for_ny_time

UTC = ZoneInfo("UTC")


def test_session_label_for_ny_time():
    pre = datetime(2026, 6, 26, 6, 0, tzinfo=NY)
    reg = datetime(2026, 6, 26, 12, 0, tzinfo=NY)
    post = datetime(2026, 6, 25, 17, 0, tzinfo=NY)
    assert session_label_for_ny_time(pre) == "PRE"
    assert session_label_for_ny_time(reg) == "REGULAR"
    assert session_label_for_ny_time(post) == "POST"


def test_pre_market_prefers_rth_close_over_stale_after_hours_trade(monkeypatch):
    """Morning pre-market with only yesterday AH trade → use RTH close, not AH."""

    monkeypatch.setattr(
        "app.core.data.quotes.current_market_state",
        lambda: MarketState(
            status=MarketStatus.PRE_MARKET,
            now_ny=datetime(2026, 6, 26, 6, 0, tzinfo=NY),
            next_transition=datetime(2026, 6, 26, 9, 30, tzinfo=NY),
        ),
    )

    snap = SimpleNamespace(
        latest_trade=SimpleNamespace(
            price=1201.32,
            timestamp=datetime(2026, 6, 25, 20, 40, 36, tzinfo=UTC),
        ),
        daily_bar=SimpleNamespace(close=1215.46, timestamp=datetime(2026, 6, 25, 4, 0, tzinfo=UTC)),
        previous_daily_bar=SimpleNamespace(close=1047.92),
        latest_quote=None,
    )

    price, state, rth = resolve_snapshot_quote(snap)
    assert price == 1215.46
    assert state == "REGULAR"
    assert rth == 1215.46


def test_refresh_with_bar_quote_during_premarket(monkeypatch):
    monkeypatch.setattr(
        "app.core.data.quotes.current_market_state",
        lambda: MarketState(
            status=MarketStatus.PRE_MARKET,
            now_ny=datetime(2026, 6, 26, 6, 0, tzinfo=NY),
            next_transition=datetime(2026, 6, 26, 9, 30, tzinfo=NY),
        ),
    )
    monkeypatch.setattr(
        "app.core.data.quotes.fetch_latest_bar_quote",
        lambda _sym: (1148.9, "PRE"),
    )
    base = YahooQuote(
        symbol="MU",
        price=1215.46,
        rth_price=1215.46,
        prev_close=1047.92,
        market_state="REGULAR",
        bid=None,
        ask=None,
    )
    refreshed = _refresh_with_bar_quote("MU", base)
    assert refreshed.price == 1148.9
    assert refreshed.market_state == "PRE"
