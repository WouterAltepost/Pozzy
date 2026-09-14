"""Calendar sync and account logic (stream B).

Everything that touches CalDAV on behalf of the app lives here so the sync job,
the routes and the calendar_write service share one code path.

`client_factory` is a module attribute so tests can swap in a fake client that
serves recorded ICS fixtures. Production code never patches it.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import select

from ...extensions import db
from ...integrations.caldav_client import CalDAVClient, CalDAVError, Occurrence, parse_occurrences
from ...models import CalendarAccount, CalendarEvent, Task
from ...settings_defaults import get_setting
from ...utils.dates import app_tz, as_utc, now_utc

log = logging.getLogger(__name__)


class PartialSyncError(Exception):
    """Some calendars synced, at least one failed. Raised after commits so the job row shows ok=False."""


class SyncError(Exception):
    """Nothing could be synced (no account, bad credentials, discovery failed)."""


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


def _secret_for(account: CalendarAccount) -> str | None:
    ref = account.secret_ref
    return current_app.config.get(ref) or os.environ.get(ref)


def _default_client_factory(account: CalendarAccount) -> CalDAVClient:
    password = _secret_for(account)
    if not password:
        raise CalDAVError(f"secret {account.secret_ref} is not set")
    return CalDAVClient(url=account.caldav_url, username=account.username, password=password)


client_factory = _default_client_factory


def ensure_account_from_env() -> CalendarAccount | None:
    """Upsert the iCloud account row from ICLOUD_* config. Returns None when not configured.

    Idempotent: keyed on username. Calendar selection and write calendar are never
    overwritten here because Wouter edits them in Settings.
    """
    username = current_app.config.get("ICLOUD_USERNAME")
    if not username:
        return None
    account = db.session.scalar(select(CalendarAccount).where(CalendarAccount.username == username))
    caldav_url = current_app.config.get("ICLOUD_CALDAV_URL") or "https://caldav.icloud.com"
    if account is None:
        account = CalendarAccount(
            name="iCloud",
            caldav_url=caldav_url,
            username=username,
            secret_ref="ICLOUD_APP_PASSWORD",
            calendar_urls=[],
            known_calendars=[],
            enabled=True,
        )
        db.session.add(account)
    elif account.caldav_url != caldav_url:
        account.caldav_url = caldav_url
    db.session.commit()
    return account


def get_account() -> CalendarAccount | None:
    account = db.session.scalar(select(CalendarAccount).order_by(CalendarAccount.created_at))
    if account is None:
        account = ensure_account_from_env()
    return account


def discover_calendars(account: CalendarAccount) -> list[dict]:
    """Refresh `known_calendars` from the server. First discovery selects every calendar."""
    client = client_factory(account)
    calendars = client.list_calendars()
    account.known_calendars = calendars
    if not account.calendar_urls:
        account.calendar_urls = [c["url"] for c in calendars]
    if not account.write_calendar_url and calendars:
        account.write_calendar_url = account.calendar_urls[0] if account.calendar_urls else calendars[0]["url"]
    db.session.commit()
    return calendars


def update_account(account: CalendarAccount, patch: dict) -> CalendarAccount:
    if "calendar_urls" in patch:
        urls = patch["calendar_urls"]
        if not isinstance(urls, list) or any(not isinstance(u, str) for u in urls):
            raise ValueError("calendar_urls must be a list of strings")
        account.calendar_urls = urls
    if "write_calendar_url" in patch:
        value = patch["write_calendar_url"]
        if value is not None and not isinstance(value, str):
            raise ValueError("write_calendar_url must be a string or null")
        account.write_calendar_url = value
    if "enabled" in patch:
        account.enabled = bool(patch["enabled"])
    if "name" in patch and isinstance(patch["name"], str) and patch["name"].strip():
        account.name = patch["name"].strip()
    db.session.commit()
    return account


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def sync_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """[local midnight today - back days, local midnight today + forward days) in UTC."""
    now = now or now_utc()
    tz = app_tz()
    today = now.astimezone(tz).date()
    back = int(get_setting("calendar_sync_days_back", 7))
    forward = int(get_setting("calendar_sync_days_forward", 30))
    start_local = datetime.combine(today - timedelta(days=back), datetime.min.time(), tzinfo=tz)
    end_local = datetime.combine(today + timedelta(days=forward), datetime.min.time(), tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _overlapping_rows(calendar_url: str, start: datetime, end: datetime) -> list[CalendarEvent]:
    return db.session.scalars(
        select(CalendarEvent).where(
            CalendarEvent.calendar_url == calendar_url,
            CalendarEvent.start < end,
            CalendarEvent.end > start,
        )
    ).all()


def _apply_occurrence(account: CalendarAccount, calendar_url: str, occ: Occurrence, etag: str | None, row: CalendarEvent | None, synced_at: datetime) -> tuple[CalendarEvent, str]:
    """Insert or update one row. Returns (row, 'inserted' | 'updated' | 'unchanged')."""
    task_id = None
    if occ.task_id:
        try:
            task_id = uuid.UUID(occ.task_id)
        except ValueError:
            task_id = None
    if row is None:
        row = CalendarEvent(
            account_id=account.id,
            calendar_url=calendar_url,
            uid=occ.uid,
            recurrence_id=occ.recurrence_id or "",
            etag=etag,
            title=occ.title,
            start=occ.start,
            end=occ.end,
            all_day=occ.all_day,
            location=occ.location,
            description=occ.description,
            task_id=task_id,
            last_synced_at=synced_at,
        )
        db.session.add(row)
        return row, "inserted"

    row.last_synced_at = synced_at
    if etag is not None and row.etag == etag and as_utc(row.start) == occ.start and as_utc(row.end) == occ.end:
        return row, "unchanged"
    row.etag = etag
    row.title = occ.title
    row.start = occ.start
    row.end = occ.end
    row.all_day = occ.all_day
    row.location = occ.location
    row.description = occ.description
    row.task_id = task_id
    return row, "updated"


def _link_task(row: CalendarEvent) -> bool:
    """Push a moved Pozzy event back onto its task (edited on the iPhone). Returns True if the task changed."""
    if not row.task_id:
        return False
    task = db.session.get(Task, row.task_id)
    if task is None or task.status != "scheduled":
        return False
    changed = False
    if task.calendar_uid != row.uid:
        task.calendar_uid = row.uid
        changed = True
    if as_utc(task.scheduled_start) != as_utc(row.start) or as_utc(task.scheduled_end) != as_utc(row.end):
        task.scheduled_start = as_utc(row.start)
        task.scheduled_end = as_utc(row.end)
        changed = True
    return changed


def sync_calendar(account: CalendarAccount, client: CalDAVClient, calendar_url: str, start: datetime, end: datetime, synced_at: datetime) -> dict:
    """Sync one calendar within the window. Raises CalDAVError if the fetch fails (nothing is deleted then)."""
    raws = client.fetch_events(calendar_url, start, end)
    existing = {(r.uid, r.recurrence_id or ""): r for r in _overlapping_rows(calendar_url, start, end)}
    seen: set[tuple[str, str]] = set()
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "deleted": 0, "skipped": 0, "tasks_updated": 0}

    for raw in raws:
        try:
            occurrences = parse_occurrences(raw.ics, start, end, default_tz=str(app_tz().key))
        except Exception as exc:  # noqa: BLE001  one broken object must not stop the calendar
            log.warning("skipping unparsable object %s: %s", raw.href, exc)
            counts["skipped"] += 1
            continue
        for occ in occurrences:
            key = (occ.uid, occ.recurrence_id or "")
            if key in seen:
                continue
            seen.add(key)
            row, outcome = _apply_occurrence(account, calendar_url, occ, raw.etag, existing.get(key), synced_at)
            counts[outcome] += 1
            if outcome != "unchanged" and _link_task(row):
                counts["tasks_updated"] += 1

    for key, row in existing.items():
        if key not in seen:
            db.session.delete(row)
            counts["deleted"] += 1
    db.session.commit()
    return counts


def _drop_unselected(account: CalendarAccount) -> int:
    """Delete rows of calendars that are no longer selected for this account."""
    selected = set(account.calendar_urls or [])
    rows = db.session.scalars(select(CalendarEvent).where(CalendarEvent.account_id == account.id)).all()
    removed = 0
    for row in rows:
        if row.calendar_url not in selected:
            db.session.delete(row)
            removed += 1
    if removed:
        db.session.commit()
    return removed


def sync_account(account: CalendarAccount, now: datetime | None = None) -> str:
    """Sync every selected calendar of one account. Commits per calendar.

    Raises SyncError when nothing could be done, PartialSyncError when at least
    one calendar failed while others succeeded. Both leave successful commits in place.
    """
    now = now or now_utc()
    start, end = sync_window(now)
    try:
        client = client_factory(account)
        if not account.calendar_urls or not account.known_calendars:
            discover_calendars(account)
    except CalDAVError as exc:
        account.last_sync_error = str(exc)
        db.session.commit()
        raise SyncError(str(exc)) from exc

    removed = _drop_unselected(account)
    totals = {"inserted": 0, "updated": 0, "unchanged": 0, "deleted": removed, "skipped": 0, "tasks_updated": 0}
    errors: list[str] = []
    for calendar_url in list(account.calendar_urls):
        try:
            counts = sync_calendar(account, client, calendar_url, start, end, now)
        except CalDAVError as exc:
            db.session.rollback()
            name = next((c["name"] for c in account.known_calendars if c["url"] == calendar_url), calendar_url)
            errors.append(f"{name}: {exc}")
            log.warning("calendar %s failed: %s", calendar_url, exc)
            continue
        for k, v in counts.items():
            totals[k] += v

    summary = ", ".join(f"{v} {k}" for k, v in totals.items() if v)
    summary = f"{len(account.calendar_urls) - len(errors)}/{len(account.calendar_urls)} calendars, {summary or 'no changes'}"
    account.last_sync_error = "; ".join(errors) if errors else None
    if len(errors) < len(account.calendar_urls) or not account.calendar_urls:
        account.last_synced_at = now
    db.session.commit()

    if errors and len(errors) == len(account.calendar_urls):
        raise SyncError(f"all calendars failed: {'; '.join(errors)}")
    if errors:
        raise PartialSyncError(f"{summary}; failed: {'; '.join(errors)}")
    return summary


def sync_all(now: datetime | None = None) -> str:
    account = get_account()
    if account is None:
        return "no calendar account configured (ICLOUD_USERNAME unset)"
    if not account.enabled:
        return f"account {account.name} disabled, skipped"
    return sync_account(account, now=now)
