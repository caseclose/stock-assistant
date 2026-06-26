from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class AddSymbolBody(BaseModel):
    symbol: str


def _svc(request):
    return request.app.state.watchlist


@router.get("")
def get_watchlist(request: Request):
    wl = _svc(request)
    market = request.app.state.market
    symbols = wl.list_symbols()
    quotes = market.quotes_for_symbols(symbols)
    items = []
    for sym in symbols:
        q = quotes.get(sym, {})
        items.append({
            "symbol": sym,
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
            "market_state": q.get("market_state"),
        })
    return {"items": items}


@router.post("")
def add_symbol(body: AddSymbolBody, request: Request):
    try:
        created = _svc(request).add(body.symbol)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "created": created, "symbol": body.symbol.strip().upper()}


@router.delete("/{symbol}")
def remove_symbol(symbol: str, request: Request):
    if not _svc(request).remove(symbol):
        raise HTTPException(404, "symbol not in watchlist")
    return {"ok": True}
