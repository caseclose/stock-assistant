"""Tests for watchlist limits."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.watchlist import MAX_SYMBOLS, WatchlistService


def test_watchlist_max_symbols(tmp_path) -> None:
    svc = WatchlistService(tmp_path / "wl.db")
    for sym in svc.list_symbols():
        svc.remove(sym)
    for i in range(MAX_SYMBOLS):
        svc.add(f"T{i}")
    try:
        svc.add("OVERFLOW")
        assert False, "expected ValueError"
    except ValueError as e:
        assert str(MAX_SYMBOLS) in str(e)
