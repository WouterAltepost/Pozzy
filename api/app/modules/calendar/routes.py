"""Calendar API (stream B).

GET    /api/calendar/events?start&end     events plus scheduled tasks in the range (local mirror only)
POST   /api/calendar/events               create on iCloud then mirror locally
PUT    /api/calendar/events/<id>          update (single events only in v1)
DELETE /api/calendar/events/<id>          delete (single events only in v1)
POST   /api/calendar/sync                 run the sync now, synchronously
GET    /api/calendar/account              the iCloud account with cached calendar list and sync status
PUT    /api/calendar/account              change calendar selection, write calendar, enabled
POST   /api/calendar/account/discover     refresh the calendar list from iCloud
"""
import uuid
from datetime import timedelta

from flask import Blueprint, request
from sqlalchemy import select

from ...auth import require_auth
from ...errors import fail, ok
from ...extensions import db
from ...integrations.caldav_client import CalDAVError, build_ics
from ...models import CalendarEvent, Task
from ...services.calendar_write import mirror_ics
from ...utils.dates import as_utc, app_tz
from . import service
from .schemas import ValidationError, parse_event_body, parse_range

bp = Blueprint("calendar", __name__, url_prefix="/api/calendar")


def _event_or_404(event_id: str):
    try:
        key = uuid.UUID(event_id)
    except ValueError:
        return None
    return db.session.get(CalendarEvent, key)


def _scheduled_tasks_between(start, end) -> list[dict]:
    start, end = as_utc(start), as_utc(end)
    stmt = (
        select(Task)
        .where(Task.scheduled_start.is_not(None), Task.scheduled_end.is_not(None), Task.status.notin_(("done", "dropped")))
        .where(Task.scheduled_start < end, Task.scheduled_end > start)
        .order_by(Task.scheduled_start)
    )
    return [t.to_dict() for t in db.session.scalars(stmt).all()]


@bp.get("/events")
@require_auth
def list_events():
    try:
        start, end = parse_range(request.args)
    except ValidationError as exc:
        return fail("validation_error", str(exc), 400)
    s, e = as_utc(start), as_utc(end)
    rows = db.session.scalars(
        select(CalendarEvent).where(CalendarEvent.start < e, CalendarEvent.end > s).order_by(CalendarEvent.start, CalendarEvent.title)
    ).all()
    return ok(
        {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "events": [r.to_dict() for r in rows],
            "tasks": _scheduled_tasks_between(start, end),
        }
    )


def _normalise_times(data: dict, existing: CalendarEvent | None = None) -> dict:
    start = data.get("start", as_utc(existing.start) if existing else None)
    end = data.get("end", as_utc(existing.end) if existing else None)
    all_day = data.get("all_day", existing.all_day if existing else False)
    if all_day:
        tz = app_tz()
        start_local = start.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = end.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        if end_local <= start_local:
            end_local = start_local + timedelta(days=1)
        start, end = start_local, end_local
    if end <= start:
        raise ValidationError("'end' must be after 'start'")
    data["start"], data["end"], data["all_day"] = start, end, all_day
    return data


@bp.post("/events")
@require_auth
def create_event():
    try:
        data = _normalise_times(parse_event_body(request.get_json(silent=True)))
    except ValidationError as exc:
        return fail("validation_error", str(exc), 400)
    account = service.get_account()
    if account is None or not account.enabled:
        return fail("calendar_not_configured", "No enabled calendar account. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD.", 409)
    calendar_url = data.get("calendar_url") or account.write_calendar_url
    if not calendar_url:
        return fail("calendar_not_configured", "No write calendar selected. Run discovery in Settings first.", 409)

    uid, ics = build_ics(
        title=data["title"], start=data["start"], end=data["end"], all_day=data["all_day"],
        location=data.get("location"), description=data.get("description"), tz=str(app_tz().key),
    )
    try:
        client = service.client_factory(account)
        client.create_event(calendar_url, ics)
    except CalDAVError as exc:
        return fail("caldav_error", f"iCloud rejected the event: {exc}", 502)
    row = mirror_ics(account, calendar_url, ics)
    db.session.commit()
    return ok(row.to_dict(), 201)


@bp.put("/events/<event_id>")
@require_auth
def update_event(event_id):
    row = _event_or_404(event_id)
    if row is None:
        return fail("not_found", "Event not found", 404)
    if row.recurrence_id:
        return fail("recurring_not_editable", "Occurrences of recurring events can only be edited on the phone in v1", 409)
    try:
        data = _normalise_times(parse_event_body(request.get_json(silent=True), partial=True), row)
    except ValidationError as exc:
        return fail("validation_error", str(exc), 400)
    account = service.get_account()
    if account is None or not account.enabled:
        return fail("calendar_not_configured", "No enabled calendar account", 409)

    _, ics = build_ics(
        title=data.get("title", row.title), start=data["start"], end=data["end"], all_day=data["all_day"],
        location=data.get("location", row.location), description=data.get("description", row.description),
        task_id=str(row.task_id) if row.task_id else None, uid=row.uid, tz=str(app_tz().key),
    )
    try:
        client = service.client_factory(account)
        client.update_event(row.calendar_url, row.uid, ics)
    except CalDAVError as exc:
        return fail("caldav_error", f"iCloud rejected the update: {exc}", 502)
    mirror_ics(account, row.calendar_url, ics)
    if row.task_id:
        task = db.session.get(Task, row.task_id)
        if task is not None and task.status == "scheduled":
            task.scheduled_start, task.scheduled_end = as_utc(data["start"]), as_utc(data["end"])
    db.session.commit()
    return ok(row.to_dict())


@bp.delete("/events/<event_id>")
@require_auth
def delete_event(event_id):
    row = _event_or_404(event_id)
    if row is None:
        return fail("not_found", "Event not found", 404)
    if row.recurrence_id:
        return fail("recurring_not_editable", "Occurrences of recurring events can only be deleted on the phone in v1", 409)
    account = service.get_account()
    if account is None or not account.enabled:
        return fail("calendar_not_configured", "No enabled calendar account", 409)
    try:
        client = service.client_factory(account)
        client.delete_event(row.calendar_url, row.uid)
    except CalDAVError as exc:
        return fail("caldav_error", f"iCloud rejected the delete: {exc}", 502)
    if row.task_id:
        task = db.session.get(Task, row.task_id)
        if task is not None and task.calendar_uid == row.uid:
            task.calendar_uid = None
    db.session.delete(row)
    db.session.commit()
    return ok({"deleted": True, "id": event_id})


@bp.post("/sync")
@require_auth
def sync_now():
    try:
        message = service.sync_all()
    except service.PartialSyncError as exc:
        db.session.rollback()
        return ok({"ok": False, "message": str(exc), "account": _account_dict()})
    except service.SyncError as exc:
        db.session.rollback()
        return fail("caldav_error", str(exc), 502)
    return ok({"ok": True, "message": message, "account": _account_dict()})


def _account_dict():
    account = service.get_account()
    return account.to_dict() if account else None


@bp.get("/account")
@require_auth
def get_account():
    return ok(_account_dict())


@bp.put("/account")
@require_auth
def put_account():
    account = service.get_account()
    if account is None:
        return fail("calendar_not_configured", "No calendar account. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD.", 409)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not body:
        return fail("validation_error", "Body must be a non-empty JSON object", 400)
    try:
        service.update_account(account, body)
    except ValueError as exc:
        return fail("validation_error", str(exc), 400)
    return ok(account.to_dict())


@bp.post("/account/discover")
@require_auth
def discover():
    account = service.get_account()
    if account is None:
        return fail("calendar_not_configured", "No calendar account. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD.", 409)
    try:
        calendars = service.discover_calendars(account)
    except CalDAVError as exc:
        return fail("caldav_error", f"Could not list calendars: {exc}", 502)
    return ok({"calendars": calendars, "account": account.to_dict()})
