"""Shared utility helpers used across the application."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Tuple

DateLike = date | datetime
DateTuple = Tuple[date, date]


def coerce_to_datetime(value: Any) -> Optional[datetime]:
    """Convert a ``date`` or ``datetime`` into a ``datetime`` instance.

    Returns ``None`` for unsupported input. Existing ``datetime`` values are
    returned unchanged to preserve timezone information and precision.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None


def normalize_date_range(candidate: Any, fallback: DateTuple) -> DateTuple:
    """Ensure ``candidate`` is a tuple of ``date`` objects, otherwise return ``fallback``.

    The candidate can contain ``date`` or ``datetime`` values. ``datetime`` inputs
    are converted to ``date`` while preserving the calendar day.
    """
    if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
        start_raw, end_raw = candidate
        start_date = start_raw.date() if isinstance(start_raw, datetime) else start_raw
        end_date = end_raw.date() if isinstance(end_raw, datetime) else end_raw
        if isinstance(start_date, date) and isinstance(end_date, date):
            return (start_date, end_date)
    return fallback


def expand_date_range_to_bounds(range_value: Any) -> Optional[Tuple[datetime, datetime]]:
    """Convert a (date|datetime, date|datetime) tuple to day bounds.

    Returns a tuple containing the start-of-day and end-of-day ``datetime``
    representation for the supplied range when possible.
    """
    if not isinstance(range_value, (list, tuple)) or len(range_value) != 2:
        return None

    start_dt = coerce_to_datetime(range_value[0])
    end_dt = coerce_to_datetime(range_value[1])
    if start_dt is None or end_dt is None:
        return None

    start_bound = datetime.combine(start_dt.date(), datetime.min.time())
    end_bound = datetime.combine(end_dt.date(), datetime.max.time())
    return (start_bound, end_bound)
