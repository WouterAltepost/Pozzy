"""deadline_urgency: daily 00:10. Flips `urgent` on open tasks due within N days (Settings deadline_urgent_days, default 3)."""
from datetime import timedelta

from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc


def flip_urgent(today) -> int:
    from sqlalchemy import select

    from ..extensions import db
    from ..models import Task
    from ..settings_defaults import get_setting

    days = int(get_setting("deadline_urgent_days") or 3)
    horizon = today + timedelta(days=days)
    rows = db.session.scalars(
        select(Task).where(Task.status.notin_(("done", "dropped")), Task.urgent.is_(False), Task.due_date.is_not(None), Task.due_date <= horizon)
    ).all()
    for task in rows:
        task.urgent = True
    return len(rows)


def run(app) -> str:
    def work():
        from ..extensions import db

        flipped = flip_urgent(today_local(now_fn()))
        db.session.commit()
        return f"flipped urgent on {flipped} task(s)"

    return run_job(app, "deadline_urgency", work)
