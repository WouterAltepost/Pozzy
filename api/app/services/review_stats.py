"""Weekly stats snapshot for the weekly review (plan 6.11).

Pure read of A's tables (goals, do's, trackers, hours, tasks, deadlines) plus
C's emails when that model exists on the branch (guarded import). Everything
is computed in Python for one week [monday, sunday]; no AI involved.
"""
import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select

from ..extensions import db
from ..models import Area, Task
from ..utils.dates import app_tz, as_utc, week_start_of

log = logging.getLogger(__name__)


def _week_bounds_utc(week_start: date) -> tuple[datetime, datetime]:
    start = datetime.combine(week_start, time.min, tzinfo=app_tz())
    return start.astimezone(timezone.utc), (start + timedelta(days=7)).astimezone(timezone.utc)


def _in_week(value, start_utc: datetime, end_utc: datetime) -> bool:
    if value is None:
        return False
    v = as_utc(value)
    return start_utc <= v < end_utc


def _email_stats(week_start: date) -> dict | None:
    try:
        from ..models import Email  # type: ignore
    except ImportError:
        return None
    try:
        start_utc, end_utc = _week_bounds_utc(week_start)
        received = db.session.scalar(select(func.count()).select_from(Email).where(Email.date >= start_utc, Email.date < end_utc)) or 0
        handled = db.session.scalar(select(func.count()).select_from(Email).where(Email.handled_at >= start_utc, Email.handled_at < end_utc)) or 0
        open_urgent = db.session.scalar(select(func.count()).select_from(Email).where(Email.handled.is_(False), func.coalesce(Email.priority_override, Email.priority) == 1)) or 0
        return {"received": int(received), "handled": int(handled), "open_urgent": int(open_urgent)}
    except Exception:
        log.exception("review_stats: email stats failed")
        return None


def compute(week_start: date) -> dict:
    from ..modules.dos import service as dos
    from ..modules.goals import service as goals
    from ..modules.hours import service as hours
    from ..modules.study import service as study
    from ..modules.trackers import service as trackers

    week_start = week_start_of(week_start)
    week_end = week_start + timedelta(days=6)
    start_utc, end_utc = _week_bounds_utc(week_start)
    areas = {a.id: a.name for a in db.session.scalars(select(Area)).all()}

    goal_rows = goals.list_goals(week_start)
    goals_out = {
        "total": len(goal_rows),
        "done": sum(1 for g in goal_rows if g.done),
        "items": [
            {"title": g.title, "area": areas.get(g.area_id), "done": g.done, "progress": f"{g.current_value:g}/{g.target_value:g}" if g.target_value else None}
            for g in goal_rows
        ],
    }

    do_rows = dos.list_dos(week_start, week_end)
    dos_out = {
        "total": len(do_rows),
        "done": sum(1 for d in do_rows if d.done),
        "rate": round(sum(1 for d in do_rows if d.done) / len(do_rows), 3) if do_rows else None,
        "rolled": sum(1 for d in do_rows if d.rolled_from_date),
        "missed": [d.title for d in do_rows if not d.done][:10],
    }

    grid = trackers.week_grid(week_start)
    trackers_out = [
        {"name": t["name"], "type": t["type"], "area": t.get("area_name"), "completion": t["completion"], "week_total": t["week_total"], "target": t.get("target_value"), "streak": t["streak"]}
        for t in grid["trackers"]
    ]

    hrs = hours.week_summary(week_start)
    hours_out = {
        "total_hours": round(hrs["total_minutes"] / 60, 1),
        "areas": [
            {"area": r["area"], "hours": round(r["minutes"] / 60, 1), "target_hours": round(r["target_minutes"] / 60, 1) if r["target_minutes"] else None}
            for r in hrs["areas"]
            if r["minutes"] or r["target_minutes"]
        ],
    }

    all_tasks = db.session.scalars(select(Task)).all()
    done_tasks = [t for t in all_tasks if t.status == "done" and _in_week(t.completed_at, start_utc, end_utc)]
    created_tasks = [t for t in all_tasks if _in_week(t.created_at, start_utc, end_utc)]
    open_tasks = [t for t in all_tasks if t.status not in ("done", "dropped")]
    overdue = [t for t in open_tasks if t.due_date and t.due_date <= week_end]
    tasks_out = {
        "done": len(done_tasks),
        "created": len(created_tasks),
        "open": len(open_tasks),
        "overdue": len(overdue),
        "done_titles": [t.title for t in done_tasks][:15],
        "done_by_area": _count_by(done_tasks, areas),
    }

    deadlines = study.list_deadlines(include_done=True)
    dl_done = [d for d in deadlines if d.done and _in_week(d.updated_at, start_utc, end_utc)]
    next_start, next_end = week_start + timedelta(days=7), week_start + timedelta(days=14)
    dl_next = [d for d in deadlines if not d.done and next_start <= as_utc(d.due_at).astimezone(app_tz()).date() < next_end + timedelta(days=7)]
    deadlines_out = {
        "done": [d.title for d in dl_done],
        "upcoming": [{"title": d.title, "course": d.course.name if d.course else None, "due": as_utc(d.due_at).astimezone(app_tz()).date().isoformat(), "task_id": str(d.task_id) if d.task_id else None} for d in dl_next[:10]],
    }

    candidates = [
        {"id": str(t.id), "title": t.title, "quadrant": t.quadrant, "due_date": t.due_date.isoformat() if t.due_date else None, "area": areas.get(t.area_id)}
        for t in sorted(open_tasks, key=lambda t: (t.due_date or date.max, as_utc(t.created_at) or datetime.max.replace(tzinfo=timezone.utc)))
    ][:25]

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "goals": goals_out,
        "dos": dos_out,
        "trackers": trackers_out,
        "hours": hours_out,
        "tasks": tasks_out,
        "deadlines": deadlines_out,
        "emails": _email_stats(week_start),
        "open_task_candidates": candidates,
    }


def _count_by(tasks: list, areas: dict) -> dict:
    out: dict = {}
    for t in tasks:
        key = areas.get(t.area_id) or "Unassigned"
        out[key] = out.get(key, 0) + 1
    return out
