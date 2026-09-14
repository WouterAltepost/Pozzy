"""Idempotent seed: four life areas and default settings.

Run with: python seeds.py   (from api/, with the venv active)
Existing rows are never overwritten so manual edits survive re-runs.
"""
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import Area, Setting

AREAS = [
    ("Study", "#2563eb", 1),
    ("Work", "#dc2626", 2),
    ("Personal", "#059669", 3),
    ("Health", "#d97706", 4),
]

DEFAULT_SETTINGS = {
    "working_window": {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00"},
    "timezone": "Europe/Amsterdam",
    "week_start": 1,
    "ai_enabled": {
        "mail_classify": True,
        "briefing": True,
        "scheduling": True,
        "capture": True,
        "weekly_review": True,
    },
    "hour_targets": {"Work": 960},
}


def seed() -> dict:
    """Insert missing areas and settings. Returns counts of rows created."""
    created = {"areas": 0, "settings": 0}

    for name, color, sort_order in AREAS:
        if db.session.scalar(select(Area).where(Area.name == name)) is None:
            db.session.add(Area(name=name, color=color, sort_order=sort_order))
            created["areas"] += 1

    for key, value in DEFAULT_SETTINGS.items():
        if db.session.scalar(select(Setting).where(Setting.key == key)) is None:
            db.session.add(Setting(key=key, value=value))
            created["settings"] += 1

    db.session.commit()
    return created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        result = seed()
    print(f"Seed done. Created {result['areas']} areas and {result['settings']} settings.")
