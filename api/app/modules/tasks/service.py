"""Task business logic. Other modules (dos, study, captures) call these, not the HTTP routes."""
import uuid
from datetime import date, timedelta

from sqlalchemy import or_, select

from ...extensions import db
from ...models import Area, Task
from ...utils.dates import now_utc, today_local
from ...utils.validation import ValidationError

STATUS_ORDER = {"inbox": 0, "todo": 1, "scheduled": 2, "done": 3, "dropped": 4}


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def _check_schedule(fields: dict, task: Task | None = None):
    start = fields.get("scheduled_start", task.scheduled_start if task else None)
    end = fields.get("scheduled_end", task.scheduled_end if task else None)
    if start and end and end <= start:
        raise ValidationError("'scheduled_end' must be after 'scheduled_start'")


def create_task(fields: dict) -> Task:
    _check_area(fields.get("area_id"))
    _check_schedule(fields)
    task = Task(**fields)
    if task.status == "done" and task.completed_at is None:
        task.completed_at = now_utc()
    db.session.add(task)
    db.session.commit()
    return task


def update_task(task: Task, fields: dict) -> Task:
    if "area_id" in fields:
        _check_area(fields["area_id"])
    _check_schedule(fields, task)
    previous_status = task.status
    for key, value in fields.items():
        setattr(task, key, value)
    if task.status == "done" and previous_status != "done":
        task.completed_at = now_utc()
    elif task.status != "done" and previous_status == "done":
        task.completed_at = None
    db.session.commit()
    return task


def complete_task(task: Task, actual_minutes: int | None = None) -> Task:
    """Mark done. Logs hours when minutes are known (estimate or actual)."""
    task.status = "done"
    task.completed_at = now_utc()
    minutes = actual_minutes if actual_minutes is not None else task.estimated_minutes
    if minutes:
        from ..hours.service import log_hours_for_task

        log_hours_for_task(task, minutes)
    db.session.commit()
    return task


def delete_task(task: Task) -> None:
    db.session.delete(task)
    db.session.commit()


def get_task(task_id) -> Task | None:
    try:
        task_uuid = uuid.UUID(str(task_id))
    except (ValueError, TypeError):
        return None
    return db.session.get(Task, task_uuid)


def list_tasks(
    *,
    status: list[str] | None = None,
    area_id=None,
    quadrant: str | None = None,
    due: str | None = None,
    q: str | None = None,
    include_closed: bool = False,
) -> list[Task]:
    stmt = select(Task)
    if status:
        stmt = stmt.where(Task.status.in_(status))
    elif not include_closed:
        stmt = stmt.where(Task.status.notin_(("done", "dropped")))
    if area_id:
        stmt = stmt.where(Task.area_id == area_id)
    if quadrant:
        from .schemas import QUADRANTS

        urgent, important = QUADRANTS[quadrant]
        stmt = stmt.where(Task.urgent == urgent, Task.important == important)
    if due:
        today = today_local()
        if due == "today":
            stmt = stmt.where(Task.due_date == today)
        elif due == "overdue":
            stmt = stmt.where(Task.due_date < today)
        elif due == "today_or_overdue":
            stmt = stmt.where(Task.due_date <= today)
        elif due == "week":
            stmt = stmt.where(Task.due_date <= today + timedelta(days=7))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
    rows = db.session.scalars(stmt).all()
    return sorted(rows, key=_sort_key)


def _sort_key(task: Task):
    return (
        STATUS_ORDER.get(task.status, 9),
        task.due_date or date.max,
        not (task.urgent and task.important),
        not task.important,
        not task.urgent,
        task.created_at or now_utc(),
    )


def tasks_due_on_or_before(day: date) -> list[Task]:
    stmt = (
        select(Task)
        .where(Task.status.notin_(("done", "dropped")), Task.due_date.is_not(None), Task.due_date <= day)
        .order_by(Task.due_date)
    )
    return db.session.scalars(stmt).all()
