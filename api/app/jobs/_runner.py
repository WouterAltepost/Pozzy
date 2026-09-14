"""Shared wrapper for background jobs (CLAUDE.md rule 5).

Every job module exposes `run(app) -> str` and delegates to `run_job`. The
wrapper opens an app context, writes a job_runs row, catches every exception so
a failing job never crashes the web process, and returns the message.
"""
import logging
from datetime import datetime, timezone

from ..extensions import db
from ..models import JobRun

log = logging.getLogger(__name__)


def run_job(app, name: str, fn) -> str:
    with app.app_context():
        row = JobRun(name=name, started_at=datetime.now(timezone.utc))
        db.session.add(row)
        db.session.commit()
        try:
            message = fn() or "ok"
            row.ok = True
        except Exception as exc:
            db.session.rollback()
            log.exception("job %s failed", name)
            message = f"{type(exc).__name__}: {exc}"[:2000]
            row.ok = False
        row.message = message
        row.finished_at = datetime.now(timezone.utc)
        db.session.commit()
        return message
