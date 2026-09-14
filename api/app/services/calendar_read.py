"""Calendar read access for the free-slot engine.

TODO(stream B): replace with the real implementation reading `calendar_events`.
Same signature, same return shape. Stream A only calls this function.
"""
from datetime import datetime


def get_events_between(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Return (start, end) aware datetime pairs for events overlapping [start, end]."""
    return []
