"""habit_reminders: every 5 minutes. Pushes a reminder for habits whose reminder time has
passed today, that are due today and not yet done or skipped.

Idempotent: `trackers.last_reminded_on` marks the day a habit was handled, so a habit gets at
most one reminder per day, and a reminder older than an hour (the server was down) is dropped
instead of arriving late.
"""
from datetime import datetime, timedelta

from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc
LATE_LIMIT = timedelta(hours=1)


def open_today(tracker, by_date, today) -> bool:
    from ..modules.trackers import service

    entry = by_date.get(today)
    if entry is not None and entry.skipped:
        return False
    if service.is_weekly(tracker):
        return not service._week_met(tracker, service._week_sum(by_date, service.week_start_of(today))) and entry is None
    return service.is_due(tracker, today, by_date) and not service._day_met(tracker, entry)


def due_reminders(now_local: datetime) -> tuple[list, list]:
    """(to_send, handled): trackers to remind now, and every tracker whose reminder time has
    passed today (all of them get last_reminded_on = today)."""
    from ..modules.trackers import service

    today = now_local.date()
    clock = now_local.strftime("%H:%M")
    pending = [t for t in service.list_trackers() if t.reminder_time and t.reminder_time <= clock and t.last_reminded_on != today]
    if not pending:
        return [], []
    history = service.entries_between([t.id for t in pending], today - timedelta(days=62), today)
    to_send = []
    for t in pending:
        hh, mm = (int(x) for x in t.reminder_time.split(":"))
        late = now_local - now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if late <= LATE_LIMIT and open_today(t, history.get(t.id, {}), today):
            to_send.append((t, service.streak(t, history.get(t.id, {}), today)))
    return to_send, pending


def payload_for(items: list) -> dict:
    if len(items) == 1:
        t, streak = items[0]
        unit = "week" if t.target_period == "week" else "day"
        body = f"Keep your {streak} {unit} streak going." if streak > 1 else "Still open for today."
        return {"title": t.name, "body": body, "url": "/", "tag": f"habit-{t.id}"}
    names = ", ".join(t.name for t, _ in items)
    return {"title": f"{len(items)} habits still open", "body": names, "url": "/", "tag": "habits"}


def run(app) -> str:
    def work():
        from ..extensions import db
        from ..integrations import webpush
        from ..settings_defaults import get_setting
        from ..utils.dates import app_tz

        if not webpush.configured():
            return "push not configured, skipped"
        if not get_setting("habit_reminders"):
            return "reminders switched off in Settings"
        now_local = now_fn().astimezone(app_tz())
        to_send, handled = due_reminders(now_local)
        today = today_local(now_fn())
        for t in handled:
            t.last_reminded_on = today
        db.session.commit()
        if not to_send:
            return f"nothing to send ({len(handled)} handled)"
        result = webpush.broadcast(payload_for(to_send))
        return f"reminded {len(to_send)} habit(s) on {result['sent']} of {result['subscriptions']} device(s)"

    return run_job(app, "habit_reminders", work)
