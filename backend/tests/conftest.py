"""Pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    db = tmp_path / "test_watchlist.db"
    os.environ["WATCHLIST_DB"] = str(db)
    from app.core.config import clear_settings_cache
    clear_settings_cache()
    yield TestClient(create_app())
    clear_settings_cache()
