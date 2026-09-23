"""Hours logging. `log_hours_for_task` is called by tasks.service.complete_task."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select

from ...extensions import db
from ...models import Area, HoursLog, Task
from ...settings_defaults import get_setting
from ...utils.dates import iso, today_local, week_start_of
from ...utils.validation import ValidationError, to_uuid


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def create_log(fields: dict) -> HoursLog:
    _check_area(fields.get("area_id"))
    if fields.get("task_id") is not None and db.session.get(Task, fields["task_id"]) is None:
        raise ValidationError("'task_id' does not match a task")
    log = HoursLog(**fields)
    db.session.add(log)
    db.session.commit()
    return log


def update_log(log: HoursLog, fields: dict) -> HoursLog:
    if "area_id" in fields:
        _check_area(fields["area_id"])
    for key, value in fields.items():
        setattr(log, key, value)
    db.session.commit()
    return log


def delete_log(log: HoursLog) -> None:
    db.session.delete(log)
    db.session.commit()


def log_hours_for_task(task: Task, minutes: int) -> HoursLog:
    """Idempotent per task: a second completion updates the existing log instead of adding one."""
    existing = db.session.scalar(select(HoursLog).where(HoursLog.task_id == task.id))
    if existing is not None:
        existing.minutes = minutes
        return existing
    log = HoursLog(
        date=today_local(),
        area_id=task.area_id,
        tags=list(task.tags or []),
        minutes=minutes,
        note=task.title,
        task_id=task.id,
        source_ref=task_ref(task.id),
    )
    db.session.add(log)
    return log


def list_logs(start: date, end: date) -> list[HoursLog]:
    stmt = select(HoursLog).where(HoursLog.date >= start, HoursLog.date <= end).order_by(HoursLog.date.desc(), HoursLog.created_at.desc())
    return db.session.scalars(stmt).all()


def week_summary(week_start: date | None = None) -> dict:
    """Minutes per area for the week, against targets from Settings (minutes per week, keyed by area name)."""
    start = week_start or week_start_of(today_local())
    end = start + timedelta(days=6)
    totals = db.session.execute(
        select(HoursLog.area_id, func.sum(HoursLog.minutes))
        .where(HoursLog.date >= start, HoursLog.date <= end)
        .group_by(HoursLog.area_id)
    ).all()
    by_area = {str(area_id) if area_id else None: int(minutes or 0) for area_id, minutes in totals}
    targets = get_setting("hour_targets") or {}
    areas = db.session.scalars(select(Area).order_by(Area.sort_order)).all()
    rows = []
    for area in areas:
        rows.append(
            {
                "area_id": str(area.id),
                "area": area.name,
                "color": area.color,
                "minutes": by_area.get(str(area.id), 0),
                "target_minutes": targets.get(area.name),
            }
        )
    rows.append({"area_id": None, "area": "Unassigned", "color": "#9ca3af", "minutes": by_area.get(None, 0), "target_minutes": None})
    per_day = db.session.execute(
        select(HoursLog.date, func.sum(HoursLog.minutes))
        .where(HoursLog.date >= start, HoursLog.date <= end)
        .group_by(HoursLog.date)
    ).all()
    return {
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "areas": rows,
        "total_minutes": sum(r["minutes"] for r in rows),
        "per_day": {d.isoformat(): int(m or 0) for d, m in per_day},
    }


# Suggestions: past agenda events and completed tasks that have no hours log yet. Computed on
# read, deterministic, no Claude involved. The window is the last SUGGEST_DAYS_BACK days.
SUGGEST_DAYS_BACK = 7
SUGGEST_MIN_MINUTES = 15
SUGGEST_MAX_MINUTES = 12 * 60


def event_ref(uid: str, recurrence_id: str | None) -> str:
    return f"event:{uid}|{recurrence_id or ''}"


def task_ref(task_id) -> str:
    return f"task:{task_id}"


def _known_refs(refs: list[str]) -> set[str]:
    """Refs that are already logged or dismissed."""
    if not refs:
        return set()
    from ...models import HoursDismissal

    logged = set(db.session.scalars(select(HoursLog.source_ref).where(HoursLog.source_ref.in_(refs))).all())
    dismissed = set(db.session.scalars(select(HoursDismissal.ref).where(HoursDismissal.ref.in_(refs))).all())
    return logged | dismissed


def suggestions(now: datetime | None = None) -> dict:
    """Candidate hours entries from the agenda and from completed tasks.

    Events: timed, already ended, not written by Pozzy for a task, between 15 minutes and 12
    hours long, in the last SUGGEST_DAYS_BACK days. The area comes from the `calendar_areas`
    setting (calendar url to area id), otherwise the user picks one when confirming.
    Tasks: completed in the window without an hours log; complete_task already logs when the
    task had an estimate, so these are the ones without minutes, offered at the default length.
    """
    from ...models import CalendarEvent
    from ...utils.dates import app_tz, as_utc, now_utc

    now = as_utc(now) if now else now_utc()
    tz = app_tz()
    window_start = datetime.combine(now.astimezone(tz).date() - timedelta(days=SUGGEST_DAYS_BACK), time.min, tzinfo=tz)
    calendar_areas = get_setting("calendar_areas") or {}
    areas = {str(a.id): a for a in db.session.scalars(select(Area)).all()}
    default_minutes = int(get_setting("default_task_minutes") or 60)

    items = []
    stmt = (
        select(CalendarEvent)
        .where(CalendarEvent.all_day.is_(False), CalendarEvent.task_id.is_(None), CalendarEvent.end <= now, CalendarEvent.end >= window_start)
        .order_by(CalendarEvent.start)
    )
    for ev in db.session.scalars(stmt).all():
        start, end = as_utc(ev.start), as_utc(ev.end)
        minutes = int(round((end - start).total_seconds() / 60))
        if minutes < SUGGEST_MIN_MINUTES or minutes > SUGGEST_MAX_MINUTES:
            continue
        area_id = calendar_areas.get(ev.calendar_url)
        if area_id not in areas:
            area_id = None
        items.append(
            {
                "ref": event_ref(ev.uid, ev.recurrence_id),
                "kind": "event",
                "date": start.astimezone(tz).date().isoformat(),
                "start": iso(start),
                "end": iso(end),
                "minutes": minutes,
                "title": ev.title,
                "location": ev.location,
                "calendar_url": ev.calendar_url,
                "area_id": area_id,
                "task_id": None,
            }
        )

    logged_tasks = set(db.session.scalars(select(HoursLog.task_id).where(HoursLog.task_id.is_not(None))).all())
    done = select(Task).where(Task.status == "done", Task.completed_at.is_not(None), Task.completed_at >= window_start, Task.completed_at <= now).order_by(Task.completed_at)
    for task in db.session.scalars(done).all():
        if task.id in logged_tasks:
            continue
        completed = as_utc(task.completed_at)
        items.append(
            {
                "ref": task_ref(task.id),
                "kind": "task",
                "date": completed.astimezone(tz).date().isoformat(),
                "start": None,
                "end": iso(completed),
                "minutes": task.estimated_minutes or default_minutes,
                "title": task.title,
                "location": None,
                "calendar_url": None,
                "area_id": str(task.area_id) if task.area_id and str(task.area_id) in areas else None,
                "task_id": str(task.id),
            }
        )

    known = _known_refs([i["ref"] for i in items])
    items = [i for i in items if i["ref"] not in known]
    items.sort(key=lambda i: (i["date"], i["start"] or i["end"]), reverse=True)
    for item in items:
        area = areas.get(item["area_id"]) if item["area_id"] else None
        item["area_name"] = area.name if area else None

    per_area: dict = {}
    for item in items:
        key = item["area_name"] or "Unassigned"
        per_area[key] = per_area.get(key, 0) + item["minutes"]
    return {
        "from": window_start.date().isoformat(),
        "to": now.astimezone(tz).date().isoformat(),
        "items": items,
        "total_minutes": sum(i["minutes"] for i in items),
        "per_area": [{"area": k, "minutes": v} for k, v in sorted(per_area.items(), key=lambda kv: -kv[1])],
    }


def accept_suggestions(picks: list[dict]) -> list[HoursLog]:
    """Create one log per accepted suggestion. A ref that is already logged is skipped, so a
    double tap or a retried request never doubles the hours."""
    refs = [p["ref"] for p in picks]
    existing = set(db.session.scalars(select(HoursLog.source_ref).where(HoursLog.source_ref.in_(refs))).all()) if refs else set()
    created = []
    for pick in picks:
        if pick["ref"] in existing:
            continue
        _check_area(pick.get("area_id"))
        task_id = None
        if pick["ref"].startswith("task:"):
            task_id = to_uuid(pick["ref"][len("task:"):])
            if task_id is not None and db.session.get(Task, task_id) is None:
                task_id = None
        log = HoursLog(
            date=pick["date"],
            minutes=pick["minutes"],
            area_id=pick.get("area_id"),
            tags=list(pick.get("tags") or []),
            note=pick.get("note"),
            task_id=task_id,
            source_ref=pick["ref"],
        )
        db.session.add(log)
        created.append(log)
        existing.add(pick["ref"])
    db.session.commit()
    return created


def dismiss_suggestions(refs: list[str]) -> int:
    from ...models import HoursDismissal

    known = set(db.session.scalars(select(HoursDismissal.ref).where(HoursDismissal.ref.in_(refs))).all()) if refs else set()
    added = 0
    for ref in refs:
        if ref in known:
            continue
        db.session.add(HoursDismissal(ref=ref))
        known.add(ref)
        added += 1
    db.session.commit()
    return added
