"""three_do_rollover: daily 00:05. Copies yesterday's undone do's to today (plan 6.5).

Idempotent: a do is copied at most once per day. `now_fn` exists so tests can freeze the clock.
"""
from datetime import timedelta

from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc


def rollover_for(today) -> dict:
    """Copy undone do's from the day before `today`. Returns counts. Caller commits."""
    from sqlalchemy import select

    from ..extensions import db
    from ..models import DailyDo

    yesterday = today - timedelta(days=1)
    pending = db.session.scalars(
        select(DailyDo).where(DailyDo.date == yesterday, DailyDo.done.is_(False)).order_by(DailyDo.position)
    ).all()
    existing = db.session.scalars(select(DailyDo).where(DailyDo.date == today)).all()
    existing_keys = {(d.title.strip().lower(), d.task_id) for d in existing}
    next_position = max((d.position for d in existing), default=0) + 1

    copied = 0
    for do in pending:
        key = (do.title.strip().lower(), do.task_id)
        if key in existing_keys:
            continue
        origin = do.rolled_from_date or do.date
        db.session.add(
            DailyDo(date=today, task_id=do.task_id, title=do.title, done=False, rolled_from_date=origin, position=next_position)
        )
        existing_keys.add(key)
        next_position += 1
        copied += 1
    return {"date": today.isoformat(), "pending": len(pending), "copied": copied}


def run(app) -> str:
    def work():
        from ..extensions import db

        result = rollover_for(today_local(now_fn()))
        db.session.commit()
        return f"rolled {result['copied']} of {result['pending']} undone do's into {result['date']}"

    return run_job(app, "three_do_rollover", work)
