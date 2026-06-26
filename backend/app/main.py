"""Stock Assistant FastAPI application."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import market as market_api, stream, symbols, watchlist
from app.core.config import get_settings
from app.services.analytics import AnalyticsService
from app.services.market_data import MarketDataService
from app.services.stream_hub import StreamHub
from app.services.watchlist import WatchlistService

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub: StreamHub = app.state.stream_hub
    poll_task = asyncio.create_task(hub.poll_loop())
    quote_task = asyncio.create_task(_watchlist_quote_loop(app))
    try:
        yield
    finally:
        poll_task.cancel()
        quote_task.cancel()
        for task in (poll_task, quote_task):
            try:
                await task
            except asyncio.CancelledError:
                pass
        hub.shutdown()


async def _watchlist_quote_loop(app: FastAPI) -> None:
    """Warm watchlist quote cache every 15s (Alpaca first, Yahoo for gaps)."""
    market = app.state.market
    watchlist = app.state.watchlist
    while True:
        try:
            symbols = watchlist.list_symbols()
            if symbols:
                await asyncio.to_thread(market.quotes_for_symbols, symbols)
        except Exception:
            log.debug("watchlist quote warm failed", exc_info=True)
        await asyncio.sleep(15)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Stock Assistant API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=(
            r"https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    market = MarketDataService()
    app.state.settings = settings
    app.state.watchlist = WatchlistService(settings.watchlist_db)
    app.state.market = market
    app.state.analytics = AnalyticsService(market)
    app.state.stream_hub = StreamHub()
    app.include_router(market_api.router)
    app.include_router(watchlist.router)
    app.include_router(symbols.router)
    app.include_router(stream.router)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "alpaca_configured": settings.has_credentials,
        }

    return app


app = create_app()
