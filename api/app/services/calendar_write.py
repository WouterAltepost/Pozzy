"""Calendar write access used when a task is scheduled (stream B implementation).

Called by stream A's tasks module. Each function writes to iCloud first and
then mirrors the change into `calendar_events` so the Agenda shows it before
the next sync. Exceptions propagate: A catches them and keeps the local
schedule, and the task's `calendar_uid` lets a later attempt retry.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from ..extensions import db
from ..integrations.caldav_client import CalDAVError, build_ics, parse_occurrences
from ..models import CalendarAccount, CalendarEvent
from ..modules.calendar import service
from ..settings_defaults import get_setting
from ..utils.dates import as_utc, now_utc

log = logging.getLogger(__name__)


def _writable_account() -> CalendarAccount | None:
    account = service.get_account()
    if account is None or not account.enabled or not account.write_calendar_url:
        return None
    return account


def _task_times(task) -> tuple[datetime, datetime]:
    start = as_utc(task.scheduled_start)
    end = as_utc(task.scheduled_end)
    if start is None:
        raise ValueError("task has no scheduled_start")
    if end is None:
        minutes = task.estimated_minutes or int(get_setting("default_task_minutes") or 60)
        end = start + timedelta(minutes=minutes)
    return start, end


def _task_ics(task, uid: str | None) -> tuple[str, str]:
    start, end = _task_times(task)
    return build_ics(
        title=task.title,
        start=start,
        end=end,
        description=task.description or None,
        task_id=str(task.id),
        uid=uid,
        tz=str(get_setting("timezone") or "Europe/Amsterdam"),
    )


def _find_row(uid: str) -> CalendarEvent | None:
    return db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == uid, CalendarEvent.recurrence_id == ""))


def mirror_ics(account: CalendarAccount, calendar_url: str, ics: str, etag: str | None = None) -> CalendarEvent | None:
    """Upsert the local row for a single-event ICS we just wrote. Caller commits."""
    far_past = datetime(2000, 1, 1, tzinfo=timezone.utc)
    far_future = datetime(2100, 1, 1, tzinfo=timezone.utc)
    occurrences = parse_occurrences(ics, far_past, far_future)
    if not occurrences:
        return None
    occ = occurrences[0]
    row = _find_row(occ.uid)
    task_id = uuid.UUID(occ.task_id) if occ.task_id else None
    if row is None:
        row = CalendarEvent(account_id=account.id, calendar_url=calendar_url, uid=occ.uid, recurrence_id="")
        db.session.add(row)
    row.calendar_url = calendar_url
    row.etag = etag
    row.title = occ.title
    row.start = occ.start
    row.end = occ.end
    row.all_day = occ.all_day
    row.location = occ.location
    row.description = occ.description
    row.task_id = task_id
    row.last_synced_at = now_utc()
    return row


def create_event(task) -> str | None:
    """Create the iCloud event for a scheduled task. Returns the VEVENT UID, or None when no calendar is configured."""
    account = _writable_account()
    if account is None:
        return None
    uid, ics = _task_ics(task, task.calendar_uid or None)
    client = service.client_factory(account)
    client.create_event(account.write_calendar_url, ics)
    mirror_ics(account, account.write_calendar_url, ics)
    return uid


def update_event(task) -> bool:
    """Rewrite the event linked via task.calendar_uid. Recreates it if it was deleted on the phone."""
    if not task.calendar_uid:
        return False
    account = _writable_account()
    if account is None:
        return False
    row = _find_row(task.calendar_uid)
    calendar_url = row.calendar_url if row else account.write_calendar_url
    uid, ics = _task_ics(task, task.calendar_uid)
    client = service.client_factory(account)
    try:
        client.update_event(calendar_url, uid, ics)
    except CalDAVError as exc:
        if "NotFound" not in str(exc):
            raise
        log.info("event %s gone from %s, recreating on write calendar", uid, calendar_url)
        calendar_url = account.write_calendar_url
        client.create_event(calendar_url, ics)
    mirror_ics(account, calendar_url, ics)
    return True


def delete_event(task) -> bool:
    """Delete the event linked via task.calendar_uid from iCloud and the local mirror."""
    if not task.calendar_uid:
        return False
    account = _writable_account()
    if account is None:
        return False
    row = _find_row(task.calendar_uid)
    calendar_url = row.calendar_url if row else account.write_calendar_url
    client = service.client_factory(account)
    deleted = client.delete_event(calendar_url, task.calendar_uid)
    for stale in db.session.scalars(select(CalendarEvent).where(CalendarEvent.uid == task.calendar_uid)).all():
        db.session.delete(stale)
    return deleted
