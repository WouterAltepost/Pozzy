# Background jobs

Registered in `api/app/scheduler.py` by stream E only. Each job module exposes `run(app) -> str`, wraps its own session, catches every exception, and writes a `job_runs` row (via `api/app/jobs/_runner.py::run_job`). All schedules are in the app timezone (Europe/Amsterdam).

| Job name | Module | Cron | Description |
|---|---|---|---|
| three_do_rollover | `app.jobs.three_do_rollover` | `5 0 * * *` | Copies yesterday's undone do's to today with `rolled_from_date`. Idempotent per day. Stream A. |
| deadline_urgency | `app.jobs.deadline_urgency` | `10 0 * * *` | Sets `urgent = true` on open tasks with `due_date` within `deadline_urgent_days` (Settings, default 3). Stream A. |
| calendar_sync | `app.jobs.calendar_sync` | `*/10 * * * *` | Mirrors the selected iCloud calendars into `calendar_events` for [today-7d, today+30d] (Settings `calendar_sync_days_back/forward`). Keyed on (calendar_url, uid, recurrence_id), skips unchanged etags, deletes vanished occurrences, pushes moved Pozzy events back onto their task. One failing calendar marks the run failed but the others still commit. Stream B. |
| mail_sync_and_classify | `app.jobs.mail_sync` | `*/15 * * * *` | Syncs every enabled IMAP account (INBOX, UID incremental, 7 day backfill on first run, read-only), then classifies new mail via `services/mail_classify.py` (Claude `classify_emails` from D, rule fallback). One failing account is recorded on `mail_accounts.last_error` and does not stop the others. Stream C. |
| daily_briefing | `app.jobs.daily_briefing` | `0 7 * * *` (Settings `briefing_time`, default 07:00; E reads it at registration) | Writes today's `daily_briefings` row via Claude, deterministic text when AI is off. Keeps an existing row (idempotent); the widget's Regenerate button forces. Stream D. |
| weekly_review_draft | `app.jobs.weekly_review_draft` | `0 18 * * 0` | Computes the week's stats snapshot and drafts the reflection and next week's focus into `weekly_reviews`. Keeps an existing draft. Stream D. |
| ai_cost_rollup | `app.jobs.ai_cost_rollup` | `55 23 * * *` | Stores today's AI spend per feature in Settings `ai_spend_daily` (90 days kept). Stream D. |
