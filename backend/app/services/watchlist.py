"""SQLite-backed watchlist persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_SYMBOLS = ("AAPL", "NVDA", "MSFT", "GOOG", "SPY")


class WatchlistService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS watchlist ("
                "symbol TEXT PRIMARY KEY, position INTEGER NOT NULL)"
            )
            cur = conn.execute("SELECT COUNT(*) AS n FROM watchlist")
            if cur.fetchone()["n"] == 0:
                for i, sym in enumerate(DEFAULT_SYMBOLS):
                    conn.execute(
                        "INSERT INTO watchlist(symbol, position) VALUES (?, ?)",
                        (sym.upper(), i),
                    )

    def list_symbols(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT symbol FROM watchlist ORDER BY position ASC, symbol ASC"
            ).fetchall()
        return [r["symbol"] for r in rows]

    def add(self, symbol: str) -> None:
        sym = symbol.strip().upper()
        if not sym:
            raise ValueError("empty symbol")
        with self._connect() as conn:
            cur = conn.execute("SELECT MAX(position) AS m FROM watchlist")
            pos = (cur.fetchone()["m"] or 0) + 1
            conn.execute(
                "INSERT OR IGNORE INTO watchlist(symbol, position) VALUES (?, ?)",
                (sym, pos),
            )

    def remove(self, symbol: str) -> bool:
        sym = symbol.strip().upper()
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM watchlist WHERE symbol = ?", (sym,))
            return cur.rowcount > 0
