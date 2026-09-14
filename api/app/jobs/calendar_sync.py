"""calendar_sync: every 10 minutes. Mirrors the selected iCloud calendars into calendar_events (plan 4.1).

Idempotent: keyed on (calendar_url, uid, recurrence_id). A calendar that fails
is skipped and reported; the others still commit. `now_fn` exists so tests can freeze the clock.
"""
from ..utils.dates import now_utc
from ._runner import run_job

now_fn = now_utc


def run(app) -> str:
    def work():
        from ..modules.calendar.service import sync_all

        return sync_all(now=now_fn())

    return run_job(app, "calendar_sync", work)
