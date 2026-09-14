"""Daily three do's."""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import Area, DailyDo, Task
from ...settings_defaults import get_setting
from ...utils.dates import iso, today_local
from ...utils.validation import ValidationError

log = logging.getLogger(__name__)


def list_dos(start: date, end: date) -> list[DailyDo]:
    stmt = select(DailyDo).where(DailyDo.date >= start, DailyDo.date <= end).order_by(DailyDo.date, DailyDo.position, DailyDo.created_at)
    return db.session.scalars(stmt).all()


def _next_position(day: date) -> int:
    rows = db.session.scalars(select(DailyDo.position).where(DailyDo.date == day)).all()
    return max(rows, default=0) + 1


def create_do(fields: dict) -> DailyDo:
    task = None
    if fields.get("task_id") is not None:
        task = db.session.get(Task, fields["task_id"])
        if task is None:
            raise ValidationError("'task_id' does not match a task")
    if not fields.get("title") and task is not None:
        fields["title"] = task.title
    if not fields.get("title"):
        raise ValidationError("'title' is required")
    fields.setdefault("date", today_local())
    if fields.get("position") is None:
        fields["position"] = _next_position(fields["date"])
    do = DailyDo(**fields)
    db.session.add(do)
    db.session.commit()
    return do


def update_do(do: DailyDo, fields: dict) -> DailyDo:
    if "task_id" in fields and fields["task_id"] is not None and db.session.get(Task, fields["task_id"]) is None:
        raise ValidationError("'task_id' does not match a task")
    was_done = do.done
    for key, value in fields.items():
        setattr(do, key, value)
    if do.done != was_done and do.task_id:
        _sync_linked_task(do)
    db.session.commit()
    return do


def _sync_linked_task(do: DailyDo) -> None:
    """Ticking a do that points at a task marks the task done; unticking reopens it."""
    from ..tasks import service as tasks

    task = db.session.get(Task, do.task_id)
    if task is None:
        return
    if do.done and task.status != "done":
        tasks.complete_task(task)
    elif not do.done and task.status == "done":
        task.status = "todo"
        task.completed_at = None


def delete_do(do: DailyDo) -> None:
    db.session.delete(do)
    db.session.commit()


def get_do(do_id) -> DailyDo | None:
    from ...utils.validation import to_uuid

    key = to_uuid(do_id)
    return db.session.get(DailyDo, key) if key else None


def completion_rate(start: date, end: date) -> dict:
    rows = list_dos(start, end)
    total = len(rows)
    done = sum(1 for r in rows if r.done)
    return {"total": total, "done": done, "rate": (done / total) if total else None}


# Suggestions -----------------------------------------------------------------


def suggestion_candidates(day: date) -> dict:
    areas = {a.id: a.name for a in db.session.scalars(select(Area)).all()}
    open_tasks = db.session.scalars(
        select(Task).where(Task.status.notin_(("done", "dropped"))).order_by(Task.due_date.nulls_last(), Task.created_at)
    ).all()
    tasks = [
        {
            "id": str(t.id),
            "title": t.title,
            "quadrant": t.quadrant,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "area": areas.get(t.area_id),
            "estimated_minutes": t.estimated_minutes,
        }
        for t in open_tasks
    ][:40]

    deadlines = []
    try:
        from ...models import Deadline

        rows = db.session.scalars(
            select(Deadline).where(Deadline.done.is_(False)).order_by(Deadline.due_at)
        ).all()
        for d in rows[:10]:
            deadlines.append(
                {"id": str(d.id), "title": d.title, "course": d.course.name if d.course else None, "due_at": iso(d.due_at), "task_id": str(d.task_id) if d.task_id else None}
            )
    except ImportError:
        pass

    goals = []
    try:
        from ...models import WeeklyGoal
        from ...utils.dates import week_start_of

        for g in db.session.scalars(select(WeeklyGoal).where(WeeklyGoal.week_start == week_start_of(day))).all():
            goals.append({"id": str(g.id), "title": g.title, "area": areas.get(g.area_id), "done": g.done})
    except ImportError:
        pass

    yesterday = day - timedelta(days=1)
    rolled = [
        {"title": d.title, "rolled_from_date": (d.rolled_from_date or d.date).isoformat(), "task_id": str(d.task_id) if d.task_id else None}
        for d in list_dos(yesterday, yesterday)
        if not d.done
    ]
    return {"date": day.isoformat(), "tasks": tasks, "deadlines": deadlines, "weekly_goals": goals, "rolled_over": rolled}


def suggest_dos_deterministic(candidates: dict, count: int) -> list[dict]:
    day = date.fromisoformat(candidates["date"])
    picks: list[dict] = []
    seen_titles = set()

    def add(title, task_id, reason):
        key = title.strip().lower()
        if key in seen_titles or len(picks) >= count:
            return
        seen_titles.add(key)
        picks.append({"title": title, "task_id": task_id, "reason": reason})

    for r in candidates.get("rolled_over", []):
        add(r["title"], r.get("task_id"), "Unfinished yesterday")
    tasks = candidates.get("tasks", [])
    for t in tasks:
        if t.get("due_date") and date.fromisoformat(t["due_date"]) <= day:
            add(t["title"], t["id"], "Due today or overdue")
    for t in tasks:
        if t.get("quadrant") == "do":
            add(t["title"], t["id"], "Urgent and important")
    for d in candidates.get("deadlines", []):
        add(d["title"], d.get("task_id"), f"Deadline {d['due_at'][:10]}" if d.get("due_at") else "Upcoming deadline")
    for t in tasks:
        if t.get("quadrant") == "schedule":
            add(t["title"], t["id"], "Important, not yet urgent")
    return picks[:count]


def suggest_dos(day: date) -> dict:
    count = int(get_setting("three_dos_count") or 3)
    candidates = suggestion_candidates(day)
    picks = suggest_dos_deterministic(candidates, count)
    source = "deterministic"
    if (get_setting("ai_enabled") or {}).get("three_dos", True) and (candidates["tasks"] or candidates["deadlines"] or candidates["rolled_over"]):
        try:
            answer = claude_client.suggest_dos(candidates, {"count": count})
        except Exception:
            log.exception("claude suggest_dos failed, using deterministic picks")
            answer = None
        validated = _validate_ai_answer(answer, candidates, count)
        if validated:
            picks, source = validated, "claude"
    return {"date": day.isoformat(), "source": source, "suggestions": picks}


def _validate_ai_answer(answer, candidates: dict, count: int) -> list[dict] | None:
    if not isinstance(answer, list) or not answer:
        return None
    allowed_ids = {t["id"] for t in candidates["tasks"]} | {d["task_id"] for d in candidates["deadlines"] if d.get("task_id")}
    out = []
    for item in answer:
        if not isinstance(item, dict) or not str(item.get("title") or "").strip():
            continue
        task_id = item.get("task_id")
        if task_id is not None and task_id not in allowed_ids:
            task_id = None
        out.append({"title": str(item["title"]).strip()[:200], "task_id": task_id, "reason": str(item.get("reason") or "")[:300]})
        if len(out) >= count:
            break
    return out or None
