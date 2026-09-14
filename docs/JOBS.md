# Background jobs

Registered in `api/app/scheduler.py` by stream E only. Each job module exposes `run(app) -> str`, wraps its own session, catches every exception, and writes a `job_runs` row (via `api/app/jobs/_runner.py::run_job`). All schedules are in the app timezone (Europe/Amsterdam).

| Job name | Module | Cron | Description |
|---|---|---|---|
| three_do_rollover | `app.jobs.three_do_rollover` | `5 0 * * *` | Copies yesterday's undone do's to today with `rolled_from_date`. Idempotent per day. Stream A. |
| deadline_urgency | `app.jobs.deadline_urgency` | `10 0 * * *` | Sets `urgent = true` on open tasks with `due_date` within `deadline_urgent_days` (Settings, default 3). Stream A. |
