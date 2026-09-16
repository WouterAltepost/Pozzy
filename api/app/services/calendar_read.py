"""Calendar read access for the free-slot engine (stream B implementation).

Reads the locally mirrored `calendar_events` table only, never CalDAV, so slot
suggestions work when iCloud is down (CLAUDE.md rule 1). Stream A calls only
`get_events_between`.
"""
from datetime import datetime

from sqlalchemy import select

from ..extensions import db
from ..models import CalendarEvent
from ..utils.dates import as_utc


def get_events_between(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Return (start, end) aware UTC pairs for busy events overlapping [start, end].

    Excluded on purpose: all-day events (deadlines, birthdays, holidays do not
    block working hours) and events Pozzy wrote for a scheduled task (the
    free-slot engine already receives those from the tasks table, and counting
    them twice would block a task's own slot when rescheduling it).
    """
    start = as_utc(start)
    end = as_utc(end)
    stmt = (
        select(CalendarEvent.start, CalendarEvent.end)
        .where(
            CalendarEvent.start < end,
            CalendarEvent.end > start,
            CalendarEvent.all_day.is_(False),
            CalendarEvent.task_id.is_(None),
        )
        .order_by(CalendarEvent.start)
    )
    return [(as_utc(s), as_utc(e)) for s, e in db.session.execute(stmt).all()]


def get_event_rows_between(start: datetime, end: datetime) -> list[dict]:
    """Timed events overlapping [start, end] with title and location, for planner context
    (what sits before and after a candidate slot). Task-linked events are included here on
    purpose: for neighbour context they are real appointments."""
    start = as_utc(start)
    end = as_utc(end)
    stmt = (
        select(CalendarEvent.title, CalendarEvent.location, CalendarEvent.start, CalendarEvent.end, CalendarEvent.task_id)
        .where(CalendarEvent.start < end, CalendarEvent.end > start, CalendarEvent.all_day.is_(False))
        .order_by(CalendarEvent.start)
    )
    return [
        {"title": title, "location": location or "", "start": as_utc(s), "end": as_utc(e), "task": task_id is not None}
        for title, location, s, e, task_id in db.session.execute(stmt).all()
    ]
