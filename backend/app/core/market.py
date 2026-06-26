"""US equity market session helpers (regular vs extended hours).

Times are NYSE conventional, expressed in America/New_York:

- Pre-market:  04:00 – 09:30 ET
- Regular:     09:30 – 16:00 ET
- After-hours: 16:00 – 20:00 ET
- Closed:      everything else (incl. weekends and US holidays)

We do NOT special-case US holidays here — a Friday after-hours followed by a
weekend just shows "closed" until next Monday's pre-market. Adding a holiday
calendar (``pandas_market_calendars``) would be a one-line swap if needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

PREMARKET_OPEN = time(4, 0)
REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
AFTERHOURS_CLOSE = time(20, 0)


class MarketStatus(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    REGULAR = "REGULAR"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"


@dataclass
class MarketState:
    status: MarketStatus
    now_ny: datetime
    next_transition: datetime  # when the status changes next (in NY time)

    @property
    def is_open(self) -> bool:
        return self.status is MarketStatus.REGULAR

    @property
    def is_extended(self) -> bool:
        return self.status in (MarketStatus.PRE_MARKET, MarketStatus.AFTER_HOURS)


def _next_weekday(dt: datetime) -> datetime:
    """Move forward (preserving time-of-day) until we land on Mon–Fri."""

    d = dt
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d = d + timedelta(days=1)
    return d


def current_market_state(now_utc: datetime | None = None) -> MarketState:
    """Return what's happening on US equity markets *right now*.

    Pass ``now_utc`` only in tests; production uses ``datetime.now`` in UTC.
    """

    if now_utc is None:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
    now_ny = now_utc.astimezone(NY)
    t = now_ny.time()
    weekday = now_ny.weekday() < 5  # Mon..Fri

    if weekday and PREMARKET_OPEN <= t < REGULAR_OPEN:
        status = MarketStatus.PRE_MARKET
        next_t = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    elif weekday and REGULAR_OPEN <= t < REGULAR_CLOSE:
        status = MarketStatus.REGULAR
        next_t = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    elif weekday and REGULAR_CLOSE <= t < AFTERHOURS_CLOSE:
        status = MarketStatus.AFTER_HOURS
        next_t = now_ny.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        status = MarketStatus.CLOSED
        # Next transition = next weekday's pre-market open at 04:00 ET.
        candidate = now_ny.replace(hour=4, minute=0, second=0, microsecond=0)
        if t >= AFTERHOURS_CLOSE or not weekday:
            candidate = candidate + timedelta(days=1)
        next_t = _next_weekday(candidate)

    return MarketState(status=status, now_ny=now_ny, next_transition=next_t)


def humanize_countdown(delta: timedelta) -> str:
    """Format a timedelta as e.g. '3h 12m' or '47m' or '12s'."""

    total = int(delta.total_seconds())
    if total < 0:
        total = 0
    if total < 60:
        return f"{total}s"
    if total < 3600:
        return f"{total // 60}m"
    h, m = divmod(total // 60, 60)
    return f"{h}h {m:02d}m"


def session_label_for_ny_time(dt_ny: datetime) -> str:
    """Map a NY timestamp to PRE | REGULAR | POST | CLOSED."""

    t = dt_ny.time()
    weekday = dt_ny.weekday() < 5
    if weekday and PREMARKET_OPEN <= t < REGULAR_OPEN:
        return "PRE"
    if weekday and REGULAR_OPEN <= t < REGULAR_CLOSE:
        return "REGULAR"
    if weekday and REGULAR_CLOSE <= t < AFTERHOURS_CLOSE:
        return "POST"
    return "CLOSED"


def clock_session_label(status: MarketStatus) -> str:
    mapping = {
        MarketStatus.PRE_MARKET: "PRE",
        MarketStatus.REGULAR: "REGULAR",
        MarketStatus.AFTER_HOURS: "POST",
        MarketStatus.CLOSED: "CLOSED",
    }
    return mapping[status]
