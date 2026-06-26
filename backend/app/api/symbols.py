from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.errors import http_bad_request
from app.services.market_data import VALID_INTERVALS

router = APIRouter(prefix="/api/symbols", tags=["symbols"])

MAX_BARS_LIMIT = 2000


@router.get("/{symbol}/bars")
def get_bars(
    symbol: str,
    request: Request,
    interval: str = "1H",
    limit: int = Query(300, ge=1, le=MAX_BARS_LIMIT),
    extended_hours: bool = True,
    before: int | None = None,
):
    if interval not in VALID_INTERVALS:
        raise HTTPException(400, f"invalid interval; choose from {list(VALID_INTERVALS)}")
    market = request.app.state.market
    try:
        df, has_more = market.fetch_bars(
            symbol.upper(),
            interval,
            limit=limit,
            extended_hours=extended_hours,
            before=before,
        )
    except Exception as e:
        raise http_bad_request(e, context=f"bars {symbol}") from e
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "extended_hours": extended_hours,
        "has_more": has_more,
        "bars": market.bars_to_records(df),
    }


@router.get("/{symbol}/analysis")
def get_analysis(
    symbol: str,
    request: Request,
    interval: str = "1H",
    extended_hours: bool = True,
):
    if interval not in VALID_INTERVALS:
        raise HTTPException(400, f"invalid interval; choose from {list(VALID_INTERVALS)}")
    analytics = request.app.state.analytics
    try:
        return analytics.analyze(symbol.upper(), interval, extended_hours=extended_hours)
    except Exception as e:
        raise http_bad_request(e, context=f"analysis {symbol}") from e
