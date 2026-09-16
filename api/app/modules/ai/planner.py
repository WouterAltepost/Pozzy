"""Plan the week: propose where open tasks, deadline prep and goal work could go.

Free slots come from scheduling/free_slots.py (deterministic). Each item is placed greedily
in priority order, then Claude may pick between the placement and up to two alternatives it is
given, never a slot of its own (CLAUDE.md rule 7). Nothing is written: the client accepts or
denies each suggestion and calls the task schedule or event create endpoints itself.
"""
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import Deadline, Task, WeeklyGoal
from ...scheduling.free_slots import find_free_slots, rank_slots_deterministic, slot_to_dict
from ...services import calendar_read
from ...settings_defaults import get_setting
from ...utils.dates import app_tz, as_utc, now_utc, today_local, week_start_of

log = logging.getLogger(__name__)

MAX_ITEMS = 12
MAX_PER_DAY = 3
PREP_MINUTES = 90
GOAL_MINUTES = 60


def _rank(task: Task) -> tuple:
    due = task.due_date or date.max
    quadrant = 0 if (task.urgent and task.important) else 1 if task.important else 2 if task.urgent else 3
    return (due, quadrant, task.created_at or now_utc())


def _candidates(start_day: date, days: int) -> list[dict]:
    """Ordered list of things worth placing. Tasks first (by due date), then deadline prep, then goals."""
    horizon = start_day + timedelta(days=days)
    default_minutes = int(get_setting("default_task_minutes") or 60)
    items: list[dict] = []
    tasks = db.session.scalars(
        select(Task).where(Task.status.in_(("inbox", "todo")), Task.scheduled_start.is_(None))
    ).all()
    for t in sorted(tasks, key=_rank)[:8]:
        items.append({
            "kind": "task", "task_id": str(t.id), "title": t.title, "area_id": str(t.area_id) if t.area_id else None,
            "minutes": t.estimated_minutes or default_minutes, "due_date": t.due_date, "before": None,
            "why": "overdue" if t.due_date and t.due_date < start_day else f"due {t.due_date.isoformat()}" if t.due_date else "open task",
            "urgent": t.urgent, "important": t.important,
        })
    prep_horizon = datetime.combine(horizon + timedelta(days=3), datetime.min.time(), tzinfo=app_tz())
    deadlines = db.session.scalars(
        select(Deadline).where(Deadline.done.is_(False), Deadline.due_at >= now_utc(), Deadline.due_at <= prep_horizon).order_by(Deadline.due_at)
    ).all()
    for d in deadlines[:3]:
        course = d.course.name if d.course is not None else ""
        items.append({
            "kind": "event", "deadline_id": str(d.id), "title": f"Prep: {d.title}" + (f" ({course})" if course else ""),
            "area_id": None, "minutes": PREP_MINUTES, "due_date": d.due_at.astimezone(app_tz()).date(), "before": as_utc(d.due_at),
            "why": f"{d.type} due {d.due_at.astimezone(app_tz()).strftime('%a %d %b %H:%M')}",
            "description": f"Prep block for the {d.type} '{d.title}'" + (f" of {course}" if course else "") + ". Suggested by Pozzy.",
        })
    ws = week_start_of(start_day)
    goals = db.session.scalars(select(WeeklyGoal).where(WeeklyGoal.week_start == ws, WeeklyGoal.done.is_(False)).order_by(WeeklyGoal.created_at)).all()
    for g in goals[:3]:
        items.append({
            "kind": "event", "goal_id": str(g.id), "title": f"Work on: {g.title}", "area_id": str(g.area_id) if g.area_id else None,
            "minutes": GOAL_MINUTES, "due_date": ws + timedelta(days=6), "before": None,
            "why": "weekly goal not met yet" + (f", {g.current_value:g} of {g.target_value:g}" if g.target_value else ""),
            "description": f"Time for the weekly goal '{g.title}'. Suggested by Pozzy.",
        })
    return items[:MAX_ITEMS]


def _scheduled_rows() -> list[tuple[Task, tuple[datetime, datetime]]]:
    stmt = select(Task).where(Task.scheduled_start.is_not(None), Task.scheduled_end.is_not(None), Task.status.notin_(("done", "dropped")))
    return [(t, (as_utc(t.scheduled_start), as_utc(t.scheduled_end))) for t in db.session.scalars(stmt).all()]


def _busy_now() -> list[tuple[datetime, datetime]]:
    stmt = select(Task.scheduled_start, Task.scheduled_end).where(
        Task.scheduled_start.is_not(None), Task.scheduled_end.is_not(None), Task.status.notin_(("done", "dropped"))
    )
    return [(as_utc(s), as_utc(e)) for s, e in db.session.execute(stmt).all()]


def _pad(intervals: list[tuple[datetime, datetime]], minutes: int) -> list[tuple[datetime, datetime]]:
    """Widen busy intervals by the planning buffer on both sides."""
    if minutes <= 0:
        return list(intervals)
    d = timedelta(minutes=minutes)
    return [(s - d, e + d) for s, e in intervals]


def _neighbours(rows: list[dict], start: datetime, end: datetime, tz) -> dict:
    """The appointment before and after a slot on the same day, with the gap in minutes."""
    start_u, end_u = as_utc(start), as_utc(end)
    day = start.astimezone(tz).date()
    same_day = [r for r in rows if r["start"].astimezone(tz).date() == day or r["end"].astimezone(tz).date() == day]
    before = [r for r in same_day if r["end"] <= start_u]
    after = [r for r in same_day if r["start"] >= end_u]
    out = {}
    if before:
        r = max(before, key=lambda x: x["end"])
        out["before"] = {"title": r["title"], "location": r["location"], "ends": r["end"].astimezone(tz).strftime("%H:%M"), "gap_minutes": int((start_u - r["end"]).total_seconds() // 60)}
    if after:
        r = min(after, key=lambda x: x["start"])
        out["after"] = {"title": r["title"], "location": r["location"], "starts": r["start"].astimezone(tz).strftime("%H:%M"), "gap_minutes": int((r["start"] - end_u).total_seconds() // 60)}
    return out


def build_plan(start_day: date | None = None, days: int = 7) -> dict:
    """Deterministic plan plus, with AI on, Claude's choice between the given options."""
    start_day = start_day or today_local()
    days = max(1, min(days, 14))
    tz = app_tz()
    from_dt = max(now_utc().astimezone(tz), datetime.combine(start_day, datetime.min.time(), tzinfo=tz))
    end_dt = datetime.combine(start_day + timedelta(days=days), datetime.min.time(), tzinfo=tz)
    try:
        events = calendar_read.get_events_between(from_dt, end_dt)
        rows = calendar_read.get_event_rows_between(from_dt, end_dt)
    except Exception:
        log.exception("calendar_read failed, planning without events")
        events, rows = [], []
    window = dict(get_setting("working_window") or {})
    window.setdefault("timezone", str(tz))
    buffer_min = int(get_setting("plan_buffer_minutes") or 0)
    scheduled = _busy_now()
    rows = rows + [{"title": t.title, "location": "", "start": s, "end": e, "task": True} for t, (s, e) in _scheduled_rows()]
    events = _pad(events, buffer_min)
    busy = list(events) + _pad(scheduled, buffer_min)
    per_day: dict[date, int] = {}
    items = []
    for cand in _candidates(start_day, days):
        slots = find_free_slots(events, [b for b in busy if b not in events], window, cand["minutes"], from_dt, days=days)
        slots = [s for s in slots if s["end"] <= end_dt and per_day.get(s["start"].date(), 0) < MAX_PER_DAY]
        if cand["before"] is not None:
            before = [s for s in slots if as_utc(s["end"]) <= cand["before"]]
            slots = before or slots
        if not slots:
            continue
        ranked = rank_slots_deterministic(slots, due_date=cand["due_date"], limit=3)
        if not ranked:
            continue
        chosen = ranked[0]
        options = [{**slot_to_dict(s), **_neighbours(rows, s["start"], s["end"], tz)} for s in ranked]
        busy.append((as_utc(chosen["start"]), as_utc(chosen["end"])))
        per_day[chosen["start"].date()] = per_day.get(chosen["start"].date(), 0) + 1
        items.append({
            "id": f"{cand['kind']}:{cand.get('task_id') or cand.get('deadline_id') or cand.get('goal_id')}",
            "kind": cand["kind"],
            "task_id": cand.get("task_id"),
            "deadline_id": cand.get("deadline_id"),
            "goal_id": cand.get("goal_id"),
            "title": cand["title"],
            "description": cand.get("description"),
            "area_id": cand["area_id"],
            "minutes": cand["minutes"],
            "start": options[0]["start"],
            "end": options[0]["end"],
            "reason": _reason(cand, chosen),
            "options": options,
            "ranked_by": "deterministic",
        })
    if items and (get_setting("ai_enabled") or {}).get("scheduling", True):
        _apply_claude(items, start_day)
    for it in items:
        it.pop("options", None)
    return {"from": from_dt.isoformat(), "to": end_dt.isoformat(), "days": days, "items": items, "considered": len(items)}


def _reason(cand: dict, slot: dict) -> str:
    bits = [cand["why"]]
    hints = slot["reason_hints"]
    if "morning" in hints:
        bits.append("morning focus time")
    if "today" in hints:
        bits.append("earliest free slot")
    elif "tomorrow" in hints:
        bits.append("tomorrow")
    if cand["due_date"] and slot["start"].date() <= cand["due_date"]:
        bits.append("before the due date")
    return ", ".join(bits).capitalize()


def _apply_claude(items: list[dict], start_day: date) -> None:
    """Let Claude pick one of the offered options per item and phrase the reason. Rule 7: options only."""
    payload = {
        "week_of": start_day.isoformat(),
        "rules": claude_client.standing_rules_list(),
        "items": [
            {"id": it["id"], "kind": it["kind"], "title": it["title"], "minutes": it["minutes"], "why": it["reason"], "options": [{"index": i, "start": o["start"], "end": o["end"], "day_label": o["day_label"], "hints": o["reason_hints"], "before": o.get("before"), "after": o.get("after")} for i, o in enumerate(it["options"])]}
            for it in items
        ],
    }
    try:
        answer = claude_client.plan_week(payload)
    except Exception:
        log.exception("plan_week raised")
        return
    if not answer:
        return
    taken: list[tuple[datetime, datetime]] = []
    kept = []
    for it in items:
        pick = answer.get(it["id"])
        if pick is not None and (pick["option"] < 0 or pick.get("place") is False):
            log.info("plan_week: %s skipped by Claude: %s", it["title"], pick.get("reason", "")[:120])
            continue
        kept.append(it)
        option = it["options"][0]
        reason = it["reason"]
        if pick is not None and 0 <= pick["option"] < len(it["options"]):
            option = it["options"][pick["option"]]
            reason = pick["reason"] or reason
        s, e = datetime.fromisoformat(option["start"]), datetime.fromisoformat(option["end"])
        if any(s < te and e > ts for ts, te in taken):
            option, reason = it["options"][0], it["reason"]
            s, e = datetime.fromisoformat(option["start"]), datetime.fromisoformat(option["end"])
        taken.append((s, e))
        it["start"], it["end"], it["reason"] = option["start"], option["end"], reason[:300]
        it["ranked_by"] = "claude" if pick is not None else "deterministic"
    items[:] = kept
