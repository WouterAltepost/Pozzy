"""Capture (quick inbox), plan 6.8.

Flow: `create_capture` stores the raw text and returns at once. `process_capture`
asks Claude for a proposal (kill switch `ai_enabled.capture`) and falls back to a
small deterministic parser, so the page works with AI off. `confirm_capture`
creates the target record through the owning module's service function, never
over HTTP. Parsed type `event` becomes a scheduled task via A's `schedule_task`
so it reaches iCloud once stream B lands and still works without it.
"""
import logging
import re
from datetime import date, datetime, timedelta, timezone

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import Area, Capture, Course, Tracker
from ...utils.dates import app_tz, now_utc, today_local, week_start_of
from ...utils.validation import ValidationError
from . import schemas

log = logging.getLogger(__name__)

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


# --- CRUD -------------------------------------------------------------------------


def create_capture(raw_text: str) -> Capture:
    row = Capture(raw_text=raw_text.strip(), status="new")
    db.session.add(row)
    db.session.commit()
    return row


def get_capture(capture_id) -> Capture | None:
    from ...utils.validation import to_uuid

    uid = to_uuid(str(capture_id))
    return db.session.get(Capture, uid) if uid else None


def list_captures(status: str | None = None, limit: int = 100) -> list[Capture]:
    stmt = select(Capture).order_by(Capture.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Capture.status == status)
    return db.session.scalars(stmt).all()


def discard_capture(capture: Capture) -> Capture:
    capture.status = "discarded"
    capture.processed_at = now_utc()
    db.session.commit()
    return capture


def delete_capture(capture: Capture) -> None:
    db.session.delete(capture)
    db.session.commit()


# --- context and deterministic parsing ---------------------------------------------


def _area_names() -> list[str]:
    return [a.name for a in db.session.scalars(select(Area).order_by(Area.sort_order)).all()]


def _tracker_rows() -> list[Tracker]:
    return db.session.scalars(select(Tracker).where(Tracker.active.is_(True)).order_by(Tracker.sort_order)).all()


def parse_context(today: date | None = None) -> dict:
    today = today or today_local()
    return {
        "today": today.isoformat(),
        "weekday": WEEKDAYS[today.weekday()].capitalize(),
        "timezone": str(app_tz()),
        "areas": _area_names(),
        "trackers": [{"name": t.name, "type": t.type, "unit": t.unit} for t in _tracker_rows()],
        "courses": [c.name for c in db.session.scalars(select(Course)).all()],
    }


def _relative_date(text: str, today: date) -> date | None:
    lower = text.lower()
    if re.search(r"\btoday\b", lower):
        return today
    if re.search(r"\btomorrow\b", lower):
        return today + timedelta(days=1)
    if re.search(r"\bnext week\b", lower):
        return week_start_of(today) + timedelta(days=7)
    for i, name in enumerate(WEEKDAYS):
        if re.search(rf"\b{name}\b|\b{name[:3]}\b", lower):
            delta = (i - today.weekday()) % 7 or 7
            return today + timedelta(days=delta)
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", lower)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def _strip_words(title: str, words: list[str]) -> str:
    out = title
    for w in words:
        out = re.sub(rf"\s*\b{re.escape(w)}\b", "", out, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", out).strip(" ,.-") or title.strip()


def parse_deterministic(text: str, context: dict) -> dict:
    """Rule-based fallback: prefixes, tracker names, relative dates, hashtags, area words."""
    today = date.fromisoformat(context["today"])
    raw = text.strip()
    lower = raw.lower()
    tags = [t.lstrip("#") for t in re.findall(r"#\w+", raw)]
    areas = context.get("areas") or []
    area = next((a for a in areas if re.search(rf"\b{re.escape(a.lower())}\b", lower)), None)
    due = _relative_date(raw, today)
    date_words = ["today", "tomorrow", "next week"] + [w for w in WEEKDAYS if re.search(rf"\b{w}\b", lower)] + [w[:3] for w in WEEKDAYS if re.search(rf"\b{w[:3]}\b", lower)]
    clean = _strip_words(re.sub(r"#\w+", "", raw), date_words)

    for name in (t["name"] for t in context.get("trackers") or []):
        if re.match(rf"^\s*{re.escape(name.lower())}\b", lower):
            rest = lower[len(name):]
            num = re.search(r"-?\d+(?:[.,]\d+)?", rest)
            value = float(num.group(0).replace(",", ".")) if num else 1
            return _proposal("tracker", {"tracker": name, "date": (due or today).isoformat(), "value": value, "note": None}, 0.6, "Starts with a tracker name")

    prefix = re.match(r"^(note|goal|event|task)\s*:\s*(.+)$", raw, flags=re.IGNORECASE | re.DOTALL)
    if prefix:
        kind, body = prefix.group(1).lower(), prefix.group(2).strip()
        clean_body = _strip_words(re.sub(r"#\w+", "", body), date_words)
        if kind == "note":
            first, _, rest = body.partition("\n")
            return _proposal("note", {"title": first[:200], "body": rest.strip() or body, "area": area, "tags": tags}, 0.7, "Prefixed with note:")
        if kind == "goal":
            week = "next" if "next week" in lower else "this"
            num = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:x|times|h|hours|km)\b", lower)
            target = float(num.group(1).replace(",", ".")) if num else None
            return _proposal("goal", {"title": clean_body[:200], "area": area, "target_value": target, "week": week}, 0.7, "Prefixed with goal:")
        if kind == "event":
            time = re.search(r"\b([01]?\d|2[0-3])[:.h]([0-5]\d)?\b", body)
            if time:
                day = due or today
                start = datetime(day.year, day.month, day.day, int(time.group(1)), int(time.group(2) or 0), tzinfo=app_tz())
                title = _strip_words(clean_body, [time.group(0), "at"])
                return _proposal("event", {"title": title[:200], "start": start.isoformat(), "end": (start + timedelta(hours=1)).isoformat(), "area": area, "description": None}, 0.6, "Prefixed with event: and has a time")
            return _proposal("task", _task_fields(clean_body, area, tags, due, lower), 0.5, "Prefixed with event: but no time found, kept as task")
        clean = clean_body

    return _proposal("task", _task_fields(clean, area, tags, due, lower), 0.5, "Default: a task")


def _task_fields(title: str, area, tags, due, lower: str) -> dict:
    est = re.search(r"\b(\d+)\s*(?:min|mins|minutes)\b", lower)
    hrs = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:h|hr|hrs|hours)\b", lower)
    minutes = int(est.group(1)) if est else (int(float(hrs.group(1).replace(",", ".")) * 60) if hrs else None)
    return {
        "title": title[:200] or "Untitled",
        "description": None,
        "area": area,
        "tags": tags,
        "urgent": bool(re.search(r"\burgent\b|\basap\b", lower)),
        "important": bool(re.search(r"\bimportant\b|\bdeadline\b|\bexam\b", lower)),
        "due_date": due.isoformat() if due else None,
        "estimated_minutes": minutes,
    }


def _proposal(kind: str, fields: dict, confidence: float, reason: str, source: str = "deterministic") -> dict:
    return {"type": kind, "fields": schemas.validate_fields(kind, fields), "confidence": confidence, "reason": reason, "source": source}


# --- processing ----------------------------------------------------------------------


def build_proposal(text: str, context: dict | None = None) -> dict:
    context = context or parse_context()
    answer = None
    try:
        answer = claude_client.parse_capture({"text": text, **context})
    except Exception:
        log.exception("parse_capture raised, using deterministic parser")
    if answer:
        try:
            return _proposal(answer["type"], answer["fields"], float(answer.get("confidence", 0.5)), answer.get("reason", ""), source="claude")
        except (PydanticValidationError, KeyError, ValueError) as exc:
            log.warning("claude capture proposal rejected: %s", exc)
    return parse_deterministic(text, context)


def process_capture(capture: Capture) -> Capture:
    if capture.status != "new":
        raise ValidationError(f"Capture is {capture.status}, only new captures can be processed")
    proposal = build_proposal(capture.raw_text)
    capture.parsed_type = proposal["type"]
    capture.parsed_json = proposal
    db.session.commit()
    return capture


# --- confirm -------------------------------------------------------------------------


def _area_id(name: str | None):
    if not name:
        return None
    row = db.session.scalar(select(Area).where(Area.name.ilike(name.strip())))
    return row.id if row else None


def confirm_capture(capture: Capture, kind: str | None = None, fields: dict | None = None) -> tuple[Capture, dict]:
    """Create the record. `kind`/`fields` override the stored proposal (Wouter edited it)."""
    if capture.status != "new":
        raise ValidationError(f"Capture is {capture.status}, only new captures can be confirmed")
    proposal = capture.parsed_json or {}
    kind = kind or proposal.get("type")
    if kind not in schemas.FIELD_MODELS:
        raise ValidationError("'type' must be one of task, event, goal, note, tracker")
    try:
        clean = schemas.validate_fields(kind, fields if fields is not None else proposal.get("fields") or {})
    except PydanticValidationError as exc:
        first = exc.errors()[0]
        raise ValidationError(f"Invalid {kind} fields: {'.'.join(str(p) for p in first['loc'])}: {first['msg']}")

    creator = {"task": _create_task, "event": _create_event, "goal": _create_goal, "note": _create_note, "tracker": _create_tracker_entry}[kind]
    ref, created = creator(capture, clean)
    capture.status = "processed"
    capture.parsed_type = kind
    capture.parsed_json = {**proposal, "type": kind, "fields": clean, "confirmed": True}
    capture.result_ref = ref
    capture.processed_at = now_utc()
    db.session.commit()
    return capture, created


def _create_task(capture: Capture, f: dict) -> tuple[str, dict]:
    from ..tasks import service as tasks

    task = tasks.create_task(
        {
            "title": f["title"],
            "description": f.get("description"),
            "area_id": _area_id(f.get("area")),
            "tags": f.get("tags") or [],
            "urgent": f.get("urgent", False),
            "important": f.get("important", False),
            "due_date": date.fromisoformat(f["due_date"]) if f.get("due_date") else None,
            "estimated_minutes": f.get("estimated_minutes"),
            "status": "todo",
            "source": "capture",
            "source_ref": str(capture.id),
        }
    )
    return f"task:{task.id}", task.to_dict()


def _create_event(capture: Capture, f: dict) -> tuple[str, dict]:
    from ..tasks import scheduling
    from ..tasks import service as tasks

    start = datetime.fromisoformat(f["start"])
    end = datetime.fromisoformat(f["end"]) if f.get("end") else start + timedelta(hours=1)
    if start.tzinfo is None:
        start = start.replace(tzinfo=app_tz())
    if end.tzinfo is None:
        end = end.replace(tzinfo=app_tz())
    # A's service layer stores UTC (SQLite drops tzinfo, readers assume UTC).
    start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    minutes = max(int((end - start).total_seconds() // 60), 5)
    task = tasks.create_task(
        {
            "title": f["title"],
            "description": f.get("description"),
            "area_id": _area_id(f.get("area")),
            "tags": [],
            "due_date": start.astimezone(app_tz()).date(),
            "estimated_minutes": minutes,
            "status": "todo",
            "source": "capture",
            "source_ref": str(capture.id),
        }
    )
    task = scheduling.schedule_task(task, start, end)
    return f"task:{task.id}", task.to_dict()


def _create_goal(capture: Capture, f: dict) -> tuple[str, dict]:
    from ..goals import service as goals

    week = week_start_of(today_local())
    if f.get("week") == "next":
        week = week + timedelta(days=7)
    goal = goals.create_goal({"title": f["title"], "area_id": _area_id(f.get("area")), "target_value": f.get("target_value"), "week_start": week})
    return f"goal:{goal.id}", goal.to_dict()


def _create_note(capture: Capture, f: dict) -> tuple[str, dict]:
    from ..notes import service as notes

    note = notes.create_note({"title": f["title"], "body": f.get("body") or "", "area_id": _area_id(f.get("area")), "tags": f.get("tags") or []})
    return f"note:{note.id}", note.to_dict()


def _create_tracker_entry(capture: Capture, f: dict) -> tuple[str, dict]:
    from ..trackers import service as trackers

    tracker = db.session.scalar(select(Tracker).where(Tracker.name.ilike(f["tracker"].strip())))
    if tracker is None:
        raise ValidationError(f"No tracker named '{f['tracker']}'")
    day = date.fromisoformat(f["date"]) if f.get("date") else today_local()
    entry = trackers.upsert_entry(tracker, day, float(f.get("value", 1)), f.get("note"))
    return f"tracker_entry:{entry.id}", {"id": str(entry.id), "tracker_id": str(tracker.id), "tracker": tracker.name, "date": day.isoformat(), "value": entry.value, "note": entry.note}
