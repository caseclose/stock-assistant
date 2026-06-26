from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["stream"])


class SubscribeBody(BaseModel):
    symbol: str
    interval: str = "1H"
    extended_hours: bool = True


@router.post("/api/stream/subscribe")
async def subscribe_stream(body: SubscribeBody, request: Request):
    hub = request.app.state.stream_hub
    try:
        await hub.subscribe(body.symbol.upper(), body.interval, body.extended_hours)
    except Exception as exc:
        return {
            "ok": False,
            "symbol": body.symbol.upper(),
            "interval": body.interval,
            "extended_hours": body.extended_hours,
            "error": str(exc),
        }
    return {
        "ok": True,
        "symbol": body.symbol.upper(),
        "interval": body.interval,
        "extended_hours": body.extended_hours,
    }


@router.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    hub = websocket.app.state.stream_hub
    q = hub.register_client()

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))

    hb = asyncio.create_task(heartbeat())
    try:
        while True:
            msg = await q.get()
            await websocket.send_text(json.dumps(msg))
    except WebSocketDisconnect:
        pass
    finally:
        hb.cancel()
        try:
            await hb
        except asyncio.CancelledError:
            pass
        hub.unregister_client(q)
