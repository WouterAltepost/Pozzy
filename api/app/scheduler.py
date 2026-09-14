"""APScheduler registration (stream E). Jobs from docs/JOBS.md.

Started only when RUN_SCHEDULER=1 (set on Railway, never in tests). Gunicorn
must stay at --workers 1: each worker would otherwise run its own scheduler and
every job twice. If more workers are ever needed, move the scheduler to a
separate process (`python -m app.scheduler`).
"""
import logging
import os
from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger

from .extensions import scheduler

log = logging.getLogger(__name__)

# (job name, module path, cron expression). daily_briefing's time comes from Settings at registration.
JOBS = [
    ("calendar_sync", "app.jobs.calendar_sync", "*/10 * * * *"),
    ("mail_sync_and_classify", "app.jobs.mail_sync", "*/15 * * * *"),
    ("three_do_rollover", "app.jobs.three_do_rollover", "5 0 * * *"),
    ("deadline_urgency", "app.jobs.deadline_urgency", "10 0 * * *"),
    ("daily_briefing", "app.jobs.daily_briefing", None),
    ("weekly_review_draft", "app.jobs.weekly_review_draft", "0 18 * * 0"),
    ("ai_cost_rollup", "app.jobs.ai_cost_rollup", "55 23 * * *"),
]

_started = False


def scheduler_enabled(app) -> bool:
    if app.config.get("TESTING"):
        return False
    return str(app.config.get("RUN_SCHEDULER") or os.environ.get("RUN_SCHEDULER") or "").strip() == "1"


def _briefing_cron(app) -> str:
    """Read Settings briefing_time (HH:MM). Falls back to 07:00 when the DB is unreachable."""
    try:
        with app.app_context():
            from .settings_defaults import get_setting

            hh, mm = str(get_setting("briefing_time") or "07:00").split(":")
            return f"{int(mm)} {int(hh)} * * *"
    except Exception:
        log.exception("briefing_time unreadable, using 07:00")
        return "0 7 * * *"


def _make_runner(app, module_path: str, name: str):
    import importlib

    module = importlib.import_module(module_path)

    def runner():
        try:
            message = module.run(app)
            log.info("job %s: %s", name, message)
        except Exception:  # run() already logs to job_runs; this only protects the scheduler thread
            log.exception("job %s raised outside run_job", name)

    runner.__name__ = f"job_{name}"
    return runner


def register_jobs(app) -> list[str]:
    """Add every job to the scheduler (idempotent by job id). Returns the job ids."""
    ids = []
    for name, module_path, cron in JOBS:
        expr = cron or _briefing_cron(app)
        trigger = CronTrigger.from_crontab(expr, timezone=app.config["TZ"])
        if scheduler.get_job(name) is not None:  # pending jobs are not deduped by replace_existing
            scheduler.remove_job(name)
        scheduler.add_job(
            _make_runner(app, module_path, name),
            trigger,
            id=name,
            name=name,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        ids.append(name)
    return ids


def start_scheduler(app) -> bool:
    """Register and start once per process. Returns True when started by this call."""
    global _started
    if _started or scheduler.running:
        return False
    # Flask's debug reloader runs create_app twice; only the serving child gets the scheduler.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true" and os.environ.get("FLASK_RUN_FROM_CLI"):
        return False
    register_jobs(app)
    scheduler.start()
    _started = True
    log.info("scheduler started at %s with jobs: %s", datetime.now(timezone.utc).isoformat(), ", ".join(j.id for j in scheduler.get_jobs()))
    return True


def scheduler_status() -> dict:
    return {
        "running": scheduler.running,
        "jobs": [
            {"id": j.id, "next_run": j.next_run_time.isoformat() if j.next_run_time else None}
            for j in scheduler.get_jobs()
        ],
    }
