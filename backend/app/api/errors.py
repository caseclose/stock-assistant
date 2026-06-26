"""API error helpers."""

from __future__ import annotations

import logging

from fastapi import HTTPException

log = logging.getLogger(__name__)


def http_bad_request(exc: Exception, *, context: str = "request") -> HTTPException:
    log.warning("%s failed: %s", context, exc)
    return HTTPException(400, "Invalid request or upstream data unavailable.")
