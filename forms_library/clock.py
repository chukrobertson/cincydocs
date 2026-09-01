from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

CINCINNATI_TIMEZONE = ZoneInfo("America/New_York")


def current_datetime() -> datetime:
    """Return the current time in the business's local timezone."""
    return datetime.now(CINCINNATI_TIMEZONE)


def current_date() -> date:
    """Return today's date in the business's local timezone."""
    return current_datetime().date()
