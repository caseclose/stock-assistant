from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/symbols", tags=["symbols"])


@router.get("/{symbol}/bars")
def get_bars(symbol: str, request: Request, interval: str = "1H", limit: int = 300):
    market = request.app.state.market
    try:
        df = market.fetch_bars(symbol.upper(), interval, limit=limit)
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "bars": market.bars_to_records(df),
    }


@router.get("/{symbol}/analysis")
def get_analysis(symbol: str, request: Request, interval: str = "1H"):
    analytics = request.app.state.analytics
    try:
        return analytics.analyze(symbol.upper(), interval)
    except Exception as e:
        raise HTTPException(400, str(e)) from e
