"""API smoke tests."""

from __future__ import annotations


def test_health(client) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "alpaca_configured" in body


def test_watchlist_crud(client) -> None:
    r = client.get("/api/watchlist")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1

    r_add = client.post("/api/watchlist", json={"symbol": "TESTX"})
    assert r_add.status_code == 200
    assert r_add.json()["created"] is True

    r_dup = client.post("/api/watchlist", json={"symbol": "TESTX"})
    assert r_dup.json()["created"] is False

    r2 = client.get("/api/watchlist")
    symbols = [i["symbol"] for i in r2.json()["items"]]
    assert "TESTX" in symbols

    r3 = client.delete("/api/watchlist/TESTX")
    assert r3.status_code == 200
