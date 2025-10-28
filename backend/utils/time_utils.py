"""Timezone utilities for consistent Africa/Harare timestamps."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

HARARE_TIMEZONE = ZoneInfo("Africa/Harare")


def now() -> datetime:
    """Return the current datetime in Africa/Harare timezone."""
    return datetime.now(HARARE_TIMEZONE)


def ensure_harare(dt: Optional[datetime] = None) -> datetime:
    """
    Ensure a datetime is timezone-aware and expressed in Africa/Harare.

    If dt is None, returns the current Harare time.
    If dt is naive, sets the Harare timezone without shifting the wall time.
    If dt has another timezone, converts it to Harare.
    """
    if dt is None:
        return now()

    if dt.tzinfo is None:
        return dt.replace(tzinfo=HARARE_TIMEZONE)

    return dt.astimezone(HARARE_TIMEZONE)
