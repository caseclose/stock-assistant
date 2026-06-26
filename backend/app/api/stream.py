from __future__ import annotations

import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["stream"])


class SubscribeBody(BaseModel):
    symbol: str
    interval: str = "1H"


@router.post("/api/stream/subscribe")
async def subscribe_stream(body: SubscribeBody, request: Request):
    hub = request.app.state.stream_hub
    await hub.subscribe(body.symbol.upper(), body.interval)
    return {"ok": True, "symbol": body.symbol.upper(), "interval": body.interval}


@router.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    hub = websocket.app.state.stream_hub
    q = hub.register_client()
    try:
        while True:
            msg = await q.get()
            await websocket.send_text(json.dumps(msg))
    except WebSocketDisconnect:
        pass
    finally:
        hub.unregister_client(q)
