"""Market status API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_market_status() -> None:
    client = TestClient(create_app())
    r = client.get("/api/market/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("PRE_MARKET", "REGULAR", "AFTER_HOURS", "CLOSED")
    assert "label_zh" in body
    assert "countdown" in body
