"""Hours logging. `log_hours_for_task` is called by tasks.service.complete_task."""
from datetime import date, timedelta

from sqlalchemy import func, select

from ...extensions import db
from ...models import Area, HoursLog, Task
from ...settings_defaults import get_setting
from ...utils.dates import today_local, week_start_of
from ...utils.validation import ValidationError


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
