"""Slot suggestion and scheduling for a task (plan 6.4, BUILD.md stream A).

Free slots are computed deterministically (scheduling/free_slots.py). Claude,
when stream D wires it, only ranks the candidates it is given and can never
introduce a slot that is not in `candidates`.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import Task
from ...scheduling.free_slots import find_free_slots, rank_slots_deterministic, slot_to_dict
from ...services import calendar_read, calendar_write
from ...settings_defaults import get_setting
from ...utils.dates import app_tz, as_utc, now_utc
from ...utils.validation import ValidationError

log = logging.getLogger(__name__)


def _duration_for(task: Task, override: int | None) -> int:
    return override or task.estimated_minutes or int(get_setting("default_task_minutes") or 60)


def _scheduled_task_intervals(exclude_id) -> list[tuple[datetime, datetime]]:
    stmt = select(Task.scheduled_start, Task.scheduled_end).where(
        Task.scheduled_start.is_not(None), Task.scheduled_end.is_not(None), Task.status.notin_(("done", "dropped")), Task.id != exclude_id
    )
    return [(as_utc(s), as_utc(e)) for s, e in db.session.execute(stmt).all()]


def candidate_slots(task: Task, *, duration_min: int | None = None, from_dt: datetime | None = None, days: int | None = None) -> tuple[list[dict], int]:
    duration = _duration_for(task, duration_min)
    days = days or int(get_setting("slot_lookahead_days") or 7)
    start = (from_dt or now_utc()).astimezone(app_tz())
    end = start + timedelta(days=days + 1)
    try:
        events = calendar_read.get_events_between(start, end)
    except Exception:  # calendar failures never break scheduling
        log.exception("calendar_read failed, scheduling without events")
        events = []
    window = dict(get_setting("working_window") or {})
    window.setdefault("timezone", str(app_tz()))
    slots = find_free_slots(events, _scheduled_task_intervals(task.id), window, duration, start, days=days)
    return slots, duration


def suggest_slots(task: Task, *, duration_min: int | None = None, from_dt: datetime | None = None, limit: int = 3) -> dict:
    slots, duration = candidate_slots(task, duration_min=duration_min, from_dt=from_dt)
    fallback = rank_slots_deterministic(slots, due_date=task.due_date, limit=limit)
    ranked = [{**slot_to_dict(s), "reason": _fallback_reason(s, task)} for s in fallback]
    ranked_by = "deterministic"

    # Deterministic pre-selection keeps the Claude payload small (max 12 spread candidates).
    shortlist = rank_slots_deterministic(slots, due_date=task.due_date, limit=12, spread=False)
    if shortlist and (get_setting("ai_enabled") or {}).get("scheduling", True):
        candidates = [slot_to_dict(s) for s in shortlist]
        try:
            answer = claude_client.rank_slots(task.to_dict(), candidates, {"limit": limit})
        except Exception:
            log.exception("claude rank_slots failed, using deterministic ranking")
            answer = None
        picked = _validate_ai_answer(answer, candidates, limit)
        if picked:
            ranked, ranked_by = picked, "claude"

    return {"task_id": str(task.id), "duration_minutes": duration, "candidates_considered": len(slots), "ranked_by": ranked_by, "slots": ranked}


def _validate_ai_answer(answer, candidates: list[dict], limit: int) -> list[dict] | None:
    """Only accept slots that exist in the candidate list (CLAUDE.md rule 7)."""
    if not isinstance(answer, list) or not answer:
        return None
    by_start = {c["start"]: c for c in candidates}
    out = []
    for item in answer:
        if not isinstance(item, dict):
            continue
        cand = by_start.get(item.get("start"))
        if cand and cand["end"] == item.get("end"):
            out.append({**cand, "reason": str(item.get("reason") or "")[:300]})
        if len(out) >= limit:
            break
    return out or None


def _fallback_reason(slot: dict, task: Task) -> str:
    hints = slot["reason_hints"]
    parts = []
    if "today" in hints:
        parts.append("earliest available")
    elif "tomorrow" in hints:
        parts.append("tomorrow")
    if "morning" in hints:
        parts.append("morning focus time")
    if task.due_date and slot["start"].date() <= task.due_date:
        parts.append("before the due date")
    elif task.due_date:
        parts.append("after the due date, nothing earlier was free")
    if "long_gap" in hints:
        parts.append("in a long free block")
    return ", ".join(parts).capitalize() if parts else "Free slot in the working window"


def schedule_task(task: Task, start: datetime, end: datetime | None) -> Task:
    if end is None:
        end = start + timedelta(minutes=_duration_for(task, None))
    if end <= start:
        raise ValidationError("'end' must be after 'start'")
    task.scheduled_start = start
    task.scheduled_end = end
    task.status = "scheduled"
    try:
        uid = calendar_write.update_event(task) if task.calendar_uid else calendar_write.create_event(task)
    except Exception:
        log.exception("calendar_write failed for task %s, kept local schedule", task.id)
        uid = None
    if isinstance(uid, str) and uid:
        task.calendar_uid = uid
    db.session.commit()
    return task


def unschedule_task(task: Task) -> Task:
    if task.calendar_uid:
        try:
            calendar_write.delete_event(task)
        except Exception:
            log.exception("calendar_write.delete_event failed for task %s", task.id)
    task.scheduled_start = None
    task.scheduled_end = None
    task.calendar_uid = None
    if task.status == "scheduled":
        task.status = "todo"
    db.session.commit()
    return task
