"""daily_briefing: daily at the Settings `briefing_time` (default 07:00). Writes today's briefing row.

Idempotent: an existing row for today is kept, so a restart does not spend a second call.
The regenerate button (POST /api/ai/briefing) forces a refresh.
"""
from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc


def run(app) -> str:
    def work():
        from ..modules.ai import briefing

        day = today_local(now_fn())
        existed = briefing.get_briefing(day) is not None
        row = briefing.generate_briefing(day, force=False)
        return f"briefing for {day} {'already existed' if existed else 'generated (' + row.source + ')'}"

    return run_job(app, "daily_briefing", work)
