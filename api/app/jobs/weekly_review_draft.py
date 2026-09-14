"""weekly_review_draft: Sunday 18:00. Computes the week's stats and drafts the reflection and next week's focus.

Idempotent: an existing draft for the week is kept (regenerate is a button on the review page).
"""
from ..utils.dates import now_utc, today_local
from ._runner import run_job

now_fn = now_utc


def run(app) -> str:
    def work():
        from ..modules.reviews import service

        week = service.week_start_of(today_local(now_fn()))
        existing = service.get_review(week)
        if existing is not None and existing.generated_at is not None:
            return f"review for week {week} already drafted"
        row = service.generate_review(week, force=False)
        return f"review for week {week} drafted ({row.reflection_source})"

    return run_job(app, "weekly_review_draft", work)
