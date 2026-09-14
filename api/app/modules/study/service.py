"""Courses, deadlines (each with an auto-created linked task), internship applications."""
from datetime import date, datetime, timedelta

from sqlalchemy import select

from ...extensions import db
from ...models import Application, Area, Course, Deadline, Task
from ...settings_defaults import get_setting
from ...utils.dates import app_tz, as_utc, today_local
from ...utils.validation import ValidationError, to_uuid

# Courses ---------------------------------------------------------------------


def list_courses(include_closed: bool = False) -> list[Course]:
    stmt = select(Course)
    if not include_closed:
        stmt = stmt.where(Course.status.in_(("active", "planned")))
    return db.session.scalars(stmt.order_by(Course.period, Course.name)).all()


def get_course(course_id) -> Course | None:
    key = to_uuid(course_id)
    return db.session.get(Course, key) if key else None


def create_course(fields: dict) -> Course:
    course = Course(**fields)
    db.session.add(course)
    db.session.commit()
    return course


def update_course(course: Course, fields: dict) -> Course:
    for key, value in fields.items():
        setattr(course, key, value)
    db.session.commit()
    return course


def delete_course(course: Course) -> None:
    for deadline in list(course.deadlines):
        _delete_linked_task(deadline)
    db.session.delete(course)
    db.session.commit()


# Deadlines -------------------------------------------------------------------


def _study_area_id():
    area = db.session.scalar(select(Area).where(Area.name == "Study"))
    return area.id if area else None


def _urgent_for(due_at: datetime) -> bool:
    days = int(get_setting("deadline_urgent_days") or 3)
    return as_utc(due_at).astimezone(app_tz()).date() <= today_local() + timedelta(days=days)


def list_deadlines(include_done: bool = False, course_id=None) -> list[Deadline]:
    stmt = select(Deadline)
    if not include_done:
        stmt = stmt.where(Deadline.done.is_(False))
    if course_id:
        stmt = stmt.where(Deadline.course_id == course_id)
    return db.session.scalars(stmt.order_by(Deadline.due_at)).all()


def get_deadline(deadline_id) -> Deadline | None:
    key = to_uuid(deadline_id)
    return db.session.get(Deadline, key) if key else None


def create_deadline(fields: dict) -> Deadline:
    course = db.session.get(Course, fields["course_id"])
    if course is None:
        raise ValidationError("'course_id' does not match a course")
    deadline = Deadline(**fields)
    db.session.add(deadline)
    db.session.flush()
    task = Task(
        title=f"{deadline.title} ({course.code or course.name})",
        area_id=_study_area_id(),
        tags=[t for t in ["deadline", course.code] if t],
        important=True,
        urgent=_urgent_for(deadline.due_at),
        status="todo",
        due_date=as_utc(deadline.due_at).astimezone(app_tz()).date(),
        source="manual",
        source_ref=f"deadline:{deadline.id}",
    )
    db.session.add(task)
    db.session.flush()
    deadline.task_id = task.id
    db.session.commit()
    return deadline


def update_deadline(deadline: Deadline, fields: dict) -> Deadline:
    if "course_id" in fields and db.session.get(Course, fields["course_id"]) is None:
        raise ValidationError("'course_id' does not match a course")
    was_done = deadline.done
    for key, value in fields.items():
        setattr(deadline, key, value)
    task = db.session.get(Task, deadline.task_id) if deadline.task_id else None
    if task is not None:
        if "title" in fields or "course_id" in fields:
            course = db.session.get(Course, deadline.course_id)
            task.title = f"{deadline.title} ({course.code or course.name})"
        if "due_at" in fields:
            task.due_date = as_utc(deadline.due_at).astimezone(app_tz()).date()
            task.urgent = task.urgent or _urgent_for(deadline.due_at)
        if deadline.done and not was_done and task.status != "done":
            from ..tasks.service import complete_task

            complete_task(task)
        elif not deadline.done and was_done and task.status == "done":
            task.status = "todo"
            task.completed_at = None
    db.session.commit()
    return deadline


def _delete_linked_task(deadline: Deadline) -> None:
    if deadline.task_id:
        task = db.session.get(Task, deadline.task_id)
        if task is not None and task.status != "done":
            db.session.delete(task)


def delete_deadline(deadline: Deadline) -> None:
    _delete_linked_task(deadline)
    db.session.delete(deadline)
    db.session.commit()


# Applications ----------------------------------------------------------------


def list_applications(include_closed: bool = True) -> list[Application]:
    stmt = select(Application)
    if not include_closed:
        stmt = stmt.where(Application.status != "rejected")
    return db.session.scalars(stmt.order_by(Application.next_step_date.nulls_last(), Application.updated_at.desc())).all()


def get_application(app_id) -> Application | None:
    key = to_uuid(app_id)
    return db.session.get(Application, key) if key else None


def create_application(fields: dict) -> Application:
    if fields.get("status") == "applied" and not fields.get("applied_at"):
        fields["applied_at"] = today_local()
    row = Application(**fields)
    db.session.add(row)
    db.session.commit()
    return row


def update_application(row: Application, fields: dict) -> Application:
    for key, value in fields.items():
        setattr(row, key, value)
    if row.status in ("applied", "interview", "offer") and row.applied_at is None:
        row.applied_at = today_local()
    db.session.commit()
    return row


def delete_application(row: Application) -> None:
    db.session.delete(row)
    db.session.commit()


# Homepage --------------------------------------------------------------------


def upcoming(days: int = 14) -> dict:
    today = today_local()
    horizon = today + timedelta(days=days)
    deadlines = [
        d.to_dict()
        for d in list_deadlines(False)
        if as_utc(d.due_at).astimezone(app_tz()).date() <= horizon
    ]
    steps = [
        a.to_dict()
        for a in db.session.scalars(
            select(Application).where(Application.next_step_date.is_not(None), Application.next_step_date <= horizon, Application.status != "rejected").order_by(Application.next_step_date)
        ).all()
    ]
    return {"today": today.isoformat(), "horizon": horizon.isoformat(), "deadlines": deadlines, "application_steps": steps}
