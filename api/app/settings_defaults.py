"""Default values for Settings keys.

Each stream adds its keys under its own comment block. `get_setting` returns the
stored value when present and the default otherwise, so pages never depend on a
seed having run. Keys already seeded in M1 (seeds.py) keep their M1 defaults here.
"""
from sqlalchemy import select

from .extensions import db
from .models import Setting

DEFAULTS: dict = {
    # M1
    "working_window": {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00"},
    "timezone": "Europe/Amsterdam",
    "week_start": 1,
    "ai_enabled": {
        "mail_classify": True,
        "briefing": True,
        "scheduling": True,
        "capture": True,
        "weekly_review": True,
        "three_dos": True,
    },
    "hour_targets": {"Work": 960},
    # Stream A (local modules)
    "briefing_time": "07:00",
    "default_task_minutes": 60,
    "slot_lookahead_days": 7,
    "deadline_urgent_days": 3,
    "three_dos_count": 3,
}


def get_setting(key: str, default=None):
    row = db.session.scalar(select(Setting).where(Setting.key == key))
    if row is not None:
        return row.value
    return DEFAULTS.get(key, default)


def get_all_settings() -> dict:
    merged = dict(DEFAULTS)
    rows = db.session.scalars(select(Setting)).all()
    for row in rows:
        merged[row.key] = row.value
    return merged
