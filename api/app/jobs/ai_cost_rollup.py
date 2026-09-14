"""ai_cost_rollup: daily 23:55. Stores today's AI spend per feature in Settings `ai_spend_daily` (last 90 days kept)."""
from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc


def run(app) -> str:
    def work():
        from ..modules.ai import spend

        day = today_local(now_fn())
        entry = spend.rollup_day(day)
        return f"{day}: {entry['calls']} call(s), {entry['failed']} failed, ${entry['cost']:.4f}"

    return run_job(app, "ai_cost_rollup", work)
