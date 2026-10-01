"""Timezone-aware time and US market session helpers."""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def market_status(now: datetime | None = None) -> str:
    """Approximate NYSE session using New York timezone and DST.

    Exchange holidays are intentionally not inferred; a future calendar provider can
    replace this isolated helper without affecting scanning logic.
    """
    ny = (now or utc_now()).astimezone(ZoneInfo("America/New_York"))
    if ny.weekday() >= 5:
        return "CLOSED"
    current = ny.time().replace(tzinfo=None)
    if time(4, 0) <= current < time(9, 30):
        return "PRE-MARKET"
    if time(9, 30) <= current < time(16, 0):
        return "OPEN"
    if time(16, 0) <= current < time(20, 0):
        return "AFTER-HOURS"
    return "CLOSED"
