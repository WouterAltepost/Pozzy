"""Daily briefing (plan 6.1). One row per day in `daily_briefings`.

`build_context` gathers today's facts from A's tables (and B's and C's when
their models exist on this branch, guarded imports). `generate_briefing` asks
Claude for the text (kill switch `ai_enabled.briefing`) and falls back to a
deterministic summary, so the widget always has something to show.
"""
import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import DailyBriefing, Task
from ...services import calendar_read
from ...utils.dates import app_tz, as_utc, iso, now_utc, today_local, week_start_of

log = logging.getLogger(__name__)

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _local_time(value) -> str:
    return as_utc(value).astimezone(app_tz()).strftime("%H:%M")


def _events_today(day: date) -> list[dict]:
    start = datetime.combine(day, time.min, tzinfo=app_tz())
    end = start + timedelta(days=1)
    try:  # stream B's table, when merged
        from ...models import CalendarEvent  # type: ignore

        rows = db.session.scalars(select(CalendarEvent).where(CalendarEvent.start < end, CalendarEvent.end > start).order_by(CalendarEvent.start)).all()
        return [
            {"title": e.title, "start": "all day" if e.all_day else _local_time(e.start), "end": None if e.all_day else _local_time(e.end), "location": e.location}
            for e in rows
        ]
    except ImportError:
        pass
    except Exception:
        log.exception("briefing: calendar_events query failed")
    try:
        pairs = calendar_read.get_events_between(start, end)
        return [{"title": "Calendar event", "start": _local_time(s), "end": _local_time(e), "location": None} for s, e in pairs]
    except Exception:
        log.exception("briefing: calendar_read failed")
        return []


def _emails_top(limit: int = 5) -> list[dict]:
    try:  # stream C's table, when merged
        from ...models import Email  # type: ignore

        rows = db.session.scalars(
            select(Email).where(Email.handled.is_(False)).order_by(Email.priority_override.nulls_last(), Email.priority.nulls_last(), Email.date.desc()).limit(limit)
        ).all()
        return [
            {"from": e.from_name or e.from_email, "subject": e.subject, "priority": e.priority_override or e.priority, "needs_reply": bool(e.needs_reply), "summary": e.summary}
            for e in rows
        ]
    except ImportError:
        return []
    except Exception:
        log.exception("briefing: emails query failed")
        return []


def build_context(day: date | None = None) -> dict:
    from ..dos import service as dos
    from ..goals import service as goals
    from ..hours import service as hours
    from ..study import service as study
    from ..tasks import service as tasks
    from ..trackers import service as trackers

    day = day or today_local()
    week = week_start_of(day)
    yesterday = day - timedelta(days=1)

    todays_dos = [{"title": d.title, "done": d.done, "rolled": bool(d.rolled_from_date)} for d in dos.list_dos(day, day)]
    due = [
        {"title": t.title, "due_date": t.due_date.isoformat(), "overdue": t.due_date < day, "quadrant": t.quadrant, "estimated_minutes": t.estimated_minutes}
        for t in tasks.tasks_due_on_or_before(day)[:10]
    ]
    scheduled = db.session.scalars(
        select(Task).where(Task.status == "scheduled", Task.scheduled_start.is_not(None)).order_by(Task.scheduled_start)
    ).all()
    scheduled_today = [
        {"title": t.title, "start": _local_time(t.scheduled_start), "end": _local_time(t.scheduled_end) if t.scheduled_end else None}
        for t in scheduled
        if as_utc(t.scheduled_start).astimezone(app_tz()).date() == day
    ]
    upcoming = study.upcoming(7)
    deadlines = [{"title": d["title"], "course": d["course_name"], "due_at": d["due_at"], "type": d["type"]} for d in upcoming["deadlines"]]
    steps = [{"company": a["company"], "role": a["role"], "next_step": a["next_step"], "date": a["next_step_date"]} for a in upcoming["application_steps"]]
    weekly_goals = [{"title": g.title, "done": g.done, "progress": f"{g.current_value:g}/{g.target_value:g}" if g.target_value else None} for g in goals.list_goals(week)]

    grid = trackers.week_grid(week)
    open_trackers = []
    for t in grid["trackers"]:
        today_cell = next((c for c in t["days"] if c["date"] == day.isoformat()), None)
        if t["type"] in ("daily_bool", "weekly_count") and today_cell and not today_cell["met"]:
            open_trackers.append({"name": t["name"], "type": t["type"], "week_total": t["week_total"], "target": t.get("target_value"), "streak": t["streak"]})

    hrs = hours.week_summary(week)
    hours_rows = [
        {"area": r["area"], "hours": round(r["minutes"] / 60, 1), "target_hours": round(r["target_minutes"] / 60, 1) if r["target_minutes"] else None}
        for r in hrs["areas"]
        if r["minutes"] or r["target_minutes"]
    ]
    y = dos.completion_rate(yesterday, yesterday)

    return {
        "date": day.isoformat(),
        "weekday": WEEKDAYS[day.weekday()],
        "dos": todays_dos,
        "tasks_due": due,
        "scheduled_tasks": scheduled_today,
        "events": _events_today(day),
        "deadlines": deadlines,
        "application_steps": steps,
        "weekly_goals": weekly_goals,
        "trackers_open": open_trackers,
        "hours": hours_rows,
        "emails": _emails_top(),
        "yesterday": {"dos_done": y["done"], "dos_total": y["total"]},
    }


def deterministic_text(ctx: dict) -> str:
    """Plain summary used when AI is off or the call fails."""
    parts = [f"{ctx['weekday']} {ctx['date']}."]
    if ctx["events"] or ctx["scheduled_tasks"]:
        items = [f"{e['start']} {e['title']}" for e in ctx["events"]] + [f"{s['start']} {s['title']} (task)" for s in ctx["scheduled_tasks"]]
        parts.append("Calendar: " + "; ".join(items) + ".")
    if ctx["dos"]:
        parts.append("Three do's: " + "; ".join(("[x] " if d["done"] else "") + d["title"] for d in ctx["dos"]) + ".")
    else:
        parts.append("No do's set for today yet.")
    overdue = [t["title"] for t in ctx["tasks_due"] if t["overdue"]]
    today_due = [t["title"] for t in ctx["tasks_due"] if not t["overdue"]]
    if overdue:
        parts.append("Overdue: " + ", ".join(overdue) + ".")
    if today_due:
        parts.append("Due today: " + ", ".join(today_due) + ".")
    if ctx["deadlines"]:
        parts.append("Deadlines this week: " + ", ".join(f"{d['title']} ({d['due_at'][:10]})" for d in ctx["deadlines"]) + ".")
    if ctx["application_steps"]:
        parts.append("Applications: " + ", ".join(f"{s['company']} {s['next_step'] or 'next step'} {s['date']}" for s in ctx["application_steps"]) + ".")
    if ctx["trackers_open"]:
        parts.append("Habits open: " + ", ".join(t["name"] for t in ctx["trackers_open"]) + ".")
    behind = [f"{h['area']} {h['hours']}/{h['target_hours']}h" for h in ctx["hours"] if h["target_hours"] and h["hours"] < h["target_hours"]]
    if behind:
        parts.append("Hours this week: " + ", ".join(behind) + ".")
    urgent_mail = [e for e in ctx["emails"] if (e.get("priority") == 1) or e.get("needs_reply")]
    if urgent_mail:
        parts.append("Mail needing attention: " + "; ".join(f"{e['from']}: {e['subject']}" for e in urgent_mail[:3]) + ".")
    return "\n\n".join(parts)


def get_briefing(day: date) -> DailyBriefing | None:
    return db.session.scalar(select(DailyBriefing).where(DailyBriefing.date == day))


def generate_briefing(day: date | None = None, force: bool = True) -> DailyBriefing:
    """Create or refresh the briefing for `day`. With force=False an existing row is returned untouched (job idempotency)."""
    day = day or today_local()
    row = get_briefing(day)
    if row is not None and not force:
        return row
    ctx = build_context(day)
    notes = [n["text"] for n in (row.notes_json or [])] if row is not None else []
    if notes:
        ctx["notes"] = notes
    text = None
    try:
        text = claude_client.write_briefing(ctx)
    except Exception:
        log.exception("write_briefing raised")
    source = "claude" if text else "deterministic"
    if not text:
        text = deterministic_text(ctx)
        if notes:
            text += "\n\nYour notes: " + " / ".join(notes)
    if row is None:
        row = DailyBriefing(date=day)
        db.session.add(row)
    row.text = text
    row.source = source
    row.model = claude_client.model_for("smart") if source == "claude" else None
    row.context_json = ctx
    row.generated_at = now_utc()
    db.session.commit()
    return row


# --- replies to the briefing --------------------------------------------------

ACTION_TYPES = ("mark_email_handled", "complete_task", "drop_task", "add_do", "add_note", "set_hour_target")


def _candidates(day: date) -> dict:
    """Ids the model may reference. Anything else in a proposed action is dropped."""
    from ..tasks import service as tasks
    from ...models import Area

    emails = []
    try:
        from ...models import Email  # type: ignore

        rows = db.session.scalars(select(Email).where(Email.handled.is_(False)).order_by(Email.priority_override.nulls_last(), Email.priority.nulls_last(), Email.date.desc()).limit(15)).all()
        emails = [{"id": str(e.id), "from": e.from_name or e.from_email, "subject": e.subject} for e in rows]
    except Exception:
        log.exception("briefing notes: emails candidates failed")
    open_tasks = tasks.list_tasks()[:30]
    areas = [a.name for a in db.session.scalars(select(Area)).all()]
    return {
        "emails": emails,
        "tasks": [{"id": str(t.id), "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None} for t in open_tasks],
        "areas": areas,
    }


def validate_actions(actions: list, candidates: dict) -> list[dict]:
    """Keep only well-formed actions that reference given ids and names. Never trusts the model."""
    email_ids = {e["id"] for e in candidates["emails"]}
    task_ids = {t["id"] for t in candidates["tasks"]}
    areas = set(candidates["areas"])
    out = []
    for a in actions or []:
        if not isinstance(a, dict) or a.get("type") not in ACTION_TYPES:
            continue
        t = a["type"]
        reason = str(a.get("reason") or "")[:200]
        if t == "mark_email_handled" and a.get("email_id") in email_ids:
            e = next(e for e in candidates["emails"] if e["id"] == a["email_id"])
            out.append({"type": t, "email_id": a["email_id"], "label": f"Mark handled: {e.get('from') or '?'}, {e['subject']}", "reason": reason})
        elif t in ("complete_task", "drop_task") and a.get("task_id") in task_ids:
            label = next(x["title"] for x in candidates["tasks"] if x["id"] == a["task_id"])
            verb = "Complete" if t == "complete_task" else "Drop"
            out.append({"type": t, "task_id": a["task_id"], "label": f"{verb} task: {label}", "reason": reason})
        elif t == "add_do" and str(a.get("title") or "").strip():
            title = str(a["title"]).strip()[:200]
            out.append({"type": t, "title": title, "label": f"Add do: {title}", "reason": reason})
        elif t == "add_note" and str(a.get("title") or "").strip():
            title = str(a["title"]).strip()[:200]
            out.append({"type": t, "title": title, "body": str(a.get("body") or "")[:2000], "label": f"Save note: {title}", "reason": reason})
        elif t == "set_hour_target" and a.get("area") in areas and a.get("hours") is not None:
            try:
                hours = max(0, min(168, int(round(float(a["hours"])))))
            except (TypeError, ValueError):
                continue
            out.append({"type": t, "area": a["area"], "hours": hours, "label": f"Set {a['area']} target to {hours}h per week", "reason": reason})
        if len(out) >= 6:
            break
    for i, a in enumerate(out):
        a["index"] = i
        a["applied"] = False
    return out


def add_note(day: date, text: str) -> DailyBriefing:
    """Store a reply to the briefing. With AI on, Claude rewrites the briefing and proposes actions;
    with AI off the note is kept and the deterministic text gains a line quoting it."""
    day = day or today_local()
    row = get_briefing(day) or generate_briefing(day, force=False)
    notes = list(row.notes_json or [])
    ctx = build_context(day)
    ctx["notes"] = [n["text"] for n in notes] + [text]
    candidates = _candidates(day)
    payload = {
        "date": ctx["date"],
        "weekday": ctx["weekday"],
        "briefing": row.text,
        "previous_notes": [n["text"] for n in notes],
        "note": text,
        "context": ctx,
        "candidates": candidates,
    }
    answer = None
    try:
        answer = claude_client.reply_briefing(payload)
    except Exception:
        log.exception("reply_briefing raised")
    if answer:
        entry = {"at": now_utc().isoformat(), "text": text, "reply": answer["reply"], "actions": validate_actions(answer["actions"], candidates), "source": "claude"}
        row.text = answer["text"]
        row.source = "claude"
        row.model = claude_client.model_for("smart")
    else:
        entry = {"at": now_utc().isoformat(), "text": text, "reply": "Noted. AI is off or unavailable, so the briefing was not rewritten; the note is kept for the next one.", "actions": [], "source": "deterministic"}
        row.text = deterministic_text(ctx) + "\n\nYour note: " + text
        row.source = "deterministic"
    notes.append(entry)
    row.notes_json = notes
    row.context_json = ctx
    row.generated_at = now_utc()
    db.session.commit()
    return row


def apply_actions(day: date, note_index: int, indexes: list[int]) -> tuple[DailyBriefing, list[dict]]:
    """Apply the selected proposed actions through the owning services. Idempotent per action."""
    from ..dos import service as dos
    from ..notes import service as notes_service
    from ..tasks import service as tasks
    from ...models import Setting, Task
    from ...utils.validation import ValidationError, to_uuid

    row = get_briefing(day)
    if row is None or not row.notes_json or note_index < 0 or note_index >= len(row.notes_json):
        raise ValidationError("No such note")
    notes = list(row.notes_json)
    entry = dict(notes[note_index])
    actions = [dict(a) for a in entry.get("actions", [])]
    results = []
    for i in indexes:
        if i < 0 or i >= len(actions):
            continue
        a = actions[i]
        if a.get("applied"):
            results.append({"index": i, "ok": True, "message": "already applied"})
            continue
        try:
            t = a["type"]
            if t == "mark_email_handled":
                from ..mail import service as mail
                from ...models import Email  # type: ignore

                email = db.session.get(Email, to_uuid(a["email_id"]))
                if email is None:
                    raise ValidationError("email not found")
                mail.update_email(email, {"handled": True})
            elif t in ("complete_task", "drop_task"):
                task = db.session.get(Task, to_uuid(a["task_id"]))
                if task is None:
                    raise ValidationError("task not found")
                if t == "complete_task":
                    tasks.complete_task(task)
                else:
                    tasks.update_task(task, {"status": "dropped"})
            elif t == "add_do":
                dos.create_do({"date": day, "title": a["title"]})
            elif t == "add_note":
                notes_service.create_note({"title": a["title"], "body": a.get("body") or "", "tags": ["briefing"]})
            elif t == "set_hour_target":
                setting = db.session.scalar(select(Setting).where(Setting.key == "hour_targets"))
                targets = dict((setting.value if setting else None) or {})
                targets[a["area"]] = int(a["hours"]) * 60
                if setting is None:
                    db.session.add(Setting(key="hour_targets", value=targets))
                else:
                    setting.value = targets
                db.session.commit()
            a["applied"] = True
            results.append({"index": i, "ok": True, "message": a["label"]})
        except Exception as exc:
            db.session.rollback()
            log.exception("briefing action failed")
            results.append({"index": i, "ok": False, "message": f"{type(exc).__name__}: {exc}"[:200]})
    entry["actions"] = actions
    notes[note_index] = entry
    row.notes_json = notes
    db.session.commit()
    return row, results
