"""Stock Assistant FastAPI application."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import stream, symbols, watchlist
from app.core.config import get_settings
from app.services.analytics import AnalyticsService
from app.services.market_data import MarketDataService
from app.services.stream_hub import StreamHub
from app.services.watchlist import WatchlistService


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub: StreamHub = app.state.stream_hub
    task = asyncio.create_task(hub.poll_loop())
    yield
    task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Stock Assistant API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
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
