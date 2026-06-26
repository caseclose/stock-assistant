"""API smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health() -> None:
    client = TestClient(create_app())
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "alpaca_configured" in body


def test_watchlist_crud() -> None:
    client = TestClient(create_app())
    r = client.get("/api/watchlist")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1

    client.post("/api/watchlist", json={"symbol": "TESTX"})
    r2 = client.get("/api/watchlist")
    symbols = [i["symbol"] for i in r2.json()["items"]]
    assert "TESTX" in symbols

    r3 = client.delete("/api/watchlist/TESTX")
    assert r3.status_code == 200
