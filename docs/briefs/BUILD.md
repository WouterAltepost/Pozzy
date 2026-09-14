# BUILD.md — Pozzy v1, parallel build after milestone 1

Read `CLAUDE.md` and `docs/POZZY_PLAN.md` fully before starting any stream. This document does not repeat module specs; it says who builds what, in which files, and how the pieces meet. Plan section 6 is the feature spec, section 5 the data model, section 7 the jobs.

## How this runs

Milestone 1 (`docs/briefs/M1-scaffold.md`) is merged to `main` and deployed before any stream starts. Every stream branches from that `main`.

Streams run as separate Claude Code sessions, each in its own git worktree:

```
git worktree add ../pozzy-A -b stream/A-local
git worktree add ../pozzy-B -b stream/B-calendar
git worktree add ../pozzy-C -b stream/C-mail
git worktree add ../pozzy-D -b stream/D-ai
```

Wave 1: A and B in parallel. Wave 2: C and D in parallel, started from `main` after A and B are merged. Stream E (integration) runs alone at the end on `main`. Wouter merges each branch with a PR when the stream reports done; E fixes what the merges break.

Each session opens with: "Read CLAUDE.md, docs/POZZY_PLAN.md, docs/briefs/BUILD.md. You are stream X. Build only what stream X owns. Report when done with the checklist in your stream's section."

## Shared contracts (all streams follow these, nobody changes them)

**Migrations.** Each stream creates exactly one Alembic migration, named `<stream>_<description>`, with `down_revision` pointing at the M1 head. Do not chain onto another stream's migration. Stream E creates the merge migration. Never edit another stream's migration.

**Models.** Each stream owns its own model files under `api/app/models/`. Foreign keys to another stream's tables are allowed only to `areas` and `tasks` (see below). Any other cross-stream link is stored as a plain UUID column with no FK constraint, resolved in E.

**Tasks is a shared table.** Stream A owns `tasks` exactly as plan section 5 lists it, including `scheduled_start`, `scheduled_end`, `calendar_uid`, `source`, `source_ref`. B, C and D read and update these columns but never alter the table. A must implement `tasks` first, in its first hour, and push the branch so B, C, D can cherry-pick the model file if they need it before A is merged.

**API envelope, auth, errors.** From M1. Every route uses `@require_auth` and the `{data, error}` envelope. No exceptions.

**Jobs.** Each job is a function `run(app) -> str` in `api/app/jobs/<name>.py` that wraps its own DB session, catches all exceptions, and writes a `job_runs` row. Registration in `api/app/scheduler.py` happens only in stream E; streams A to D add a line to `docs/JOBS.md` instead: job name, module path, cron schedule, one-line description.

**Vue routes and nav.** Streams add nothing to `web/src/router/index.js` or `App.vue`. Each stream writes its route entries into `docs/ROUTES.md` (path, view file, nav label, nav order). Stream E wires them.

**Homepage widgets.** Each stream that contributes to the homepage builds a self-contained component `web/src/components/home/<Name>Widget.vue` that fetches its own data and renders nothing if the API call fails. It lists the widget in `docs/WIDGETS.md` with the intended order. Stream E assembles `HomeView.vue`.

**Settings.** Read via `GET /api/settings`; each stream may add keys with defaults in `api/app/settings_defaults.py` under a stream-specific comment block. No stream changes another stream's keys.

**AI calls.** Only through `api/app/integrations/claude_client.py` (stream D). In wave 1, streams A and B that need Claude (slot ranking, three-do suggestion) call a stub `claude_client.rank_slots(...)`/`suggest_dos(...)` that D will implement; A and B define the function signatures they need in `docs/AI_CONTRACTS.md` with input and output JSON shapes, and implement a deterministic fallback so the feature works without D.

**Tests.** Every stream adds pytest tests under `api/tests/<stream>/`. Green before reporting done. No stream edits another stream's tests.

**Styling.** Plain CSS, one `web/src/styles/base.css` from M1. Streams add module-scoped styles in their own `.vue` files only.

## Stream A — Local modules

Owns: Tasks, Goals (weekly goals + three do's), Trackers, Hours, Notes, Study, Settings page. Plan sections 6.4 to 6.7, 6.9, 6.10, 6.12 (settings UI only; calendar and mail account forms are B's and C's).

Files: `api/app/models/{task,daily_do,weekly_goal,tracker,tracker_entry,hours_log,note,course,deadline,application}.py`, `api/app/modules/{tasks,dos,goals,trackers,hours,notes,study,settings}/`, `api/app/jobs/{three_do_rollover,deadline_urgency}.py`, `api/app/scheduling/free_slots.py` (the deterministic free-slot engine, see below), `web/src/views/{Tasks,Goals,Trackers,Hours,Notes,Study,Settings}View.vue`, `web/src/stores/{tasks,goals,trackers,hours,notes,study,settings}.js`, `web/src/api/*.js` for the same, `web/src/components/home/{ThreeDos,TasksDue,TrackerRow,HoursWeek,WeeklyGoals,Deadlines}Widget.vue`.

Free-slot engine lives in A because it only needs tasks and settings; B feeds it events. Signature: `find_free_slots(events: list[tuple[datetime, datetime]], scheduled_tasks: list[tuple[datetime, datetime]], window: dict, duration_min: int, from_dt: datetime, days: int = 7) -> list[dict]` returning `[{start, end, day_label, reason_hints}]`. Pure function, no DB. At least 8 unit tests including: empty calendar, fully booked day, task longer than any gap, window crossing DST change, weekend excluded.

Endpoint `POST /api/tasks/{id}/suggest-slot` in A: loads events via a function `get_events_between(start, end)` that A defines in `api/app/services/calendar_read.py` returning `[]` until B implements it. Returns top 3 slots. Ranking: deterministic (earliest slot on the due-date side, prefer mornings) until D adds Claude ranking. `POST /api/tasks/{id}/schedule` sets `scheduled_start/end` and calls `calendar_write.create_event(task)` from `api/app/services/calendar_write.py`, a no-op stub until B fills it.

Done checklist: all CRUD endpoints with tests; Eisenhower board with drag between quadrants; rollover job tested with a frozen clock across midnight; trackers weekly grid for bool and count, line chart for numeric/duration (use a tiny SVG chart, no chart library); hours timer; study deadline creates linked task; `docs/ROUTES.md`, `docs/WIDGETS.md`, `docs/JOBS.md`, `docs/AI_CONTRACTS.md` entries written; `docs/PROGRESS.md` stream A section updated.

## Stream B — Calendar

Owns: iCloud CalDAV integration, Agenda module. Plan sections 4.1, 6.2.

Files: `api/app/models/{calendar_account,calendar_event}.py`, `api/app/integrations/caldav_client.py`, `api/app/services/calendar_read.py` (replaces A's stub: same signature), `api/app/services/calendar_write.py` (replaces A's stub), `api/app/modules/calendar/`, `api/app/jobs/calendar_sync.py`, `web/src/views/AgendaView.vue`, `web/src/stores/calendar.js`, `web/src/api/calendar.js`, `web/src/components/agenda/*`, `web/src/components/home/TodayEventsWidget.vue`, `web/src/components/settings/CalendarAccounts.vue` (A's Settings page will mount this component by name; B documents the import path in `docs/ROUTES.md`).

Sync rules from plan 4.1. Must survive one calendar failing. Must handle all-day events, recurring events (expand occurrences within the sync window using the `recurring-ical-events` or `icalendar` library; store each occurrence with `uid` + `recurrence_id`), and timezone conversion (store UTC, display Europe/Amsterdam). Write-back creates a VEVENT with `X-POZZY-TASK-ID` property so a synced-back event can be linked to its task.

Testing: unit tests with recorded CalDAV responses (fixtures), no live calls in pytest. One manual script `api/scripts/caldav_smoke.py` that lists calendars and the next 5 events against the real account, for Wouter to run once.

Done checklist: sync job idempotent (run twice, same rows); week and day views; create, edit, delete from Agenda round-trips to iPhone (Wouter verifies manually); `calendar_read.get_events_between` returns real events so A's slot suggestions become correct with no change in A; `docs/*.md` entries; PROGRESS.md stream B section.

## Stream C — Mail

Owns: IMAP integration, classification pipeline plumbing, Mail module. Plan sections 4.2, 6.3.

Files: `api/app/models/{mail_account,email}.py`, `api/app/integrations/imap_client.py`, `api/app/modules/mail/`, `api/app/jobs/mail_sync.py`, `api/app/services/mail_classify.py` (calls `claude_client.classify_emails(batch)` from D; until D exists, a rule-based fallback: priority 3, category by simple sender heuristics, `needs_reply` false), `web/src/views/MailView.vue`, `web/src/stores/mail.js`, `web/src/api/mail.js`, `web/src/components/mail/*`, `web/src/components/home/TopEmailsWidget.vue`, `web/src/components/settings/MailAccounts.vue`.

Rules: read-only IMAP (CLAUDE.md rule 8), `MAIL_ACCOUNTS_JSON` parsed at startup into `mail_accounts` rows (upsert by email), INBOX only, UID-based incremental fetch, 7-day backfill on first run per account, body snippet max 2 KB of text/plain (fall back to stripped text/html), never fetch attachments, never store full bodies. "Create task from email" calls A's tasks API with `source="email"`, `source_ref=email.id`.

Testing: `imap-tools` mocked with fixture messages including multipart, HTML-only, non-UTF8 subject encoding, and a message with no Date header. Smoke script `api/scripts/imap_smoke.py` that connects to each account and prints the 3 newest subjects.

Done checklist: sync 4 accounts idempotently; unified inbox with filters; overrides survive re-classification; task-from-email works; `docs/*.md` entries; PROGRESS.md stream C section.

## Stream D — AI

Owns: everything that calls Anthropic. Plan section 4.3, plus Capture (6.8), daily briefing (part of 6.1), weekly review generation (part of 6.11), slot ranking, three-do suggestion, email classification implementation.

Files: `api/app/integrations/claude_client.py` (implements every signature in `docs/AI_CONTRACTS.md` from A, B, C, plus its own), `docs/prompts/*.md` (one file per feature, with the JSON schema the model must return), `api/app/models/{capture,weekly_review}.py`, `api/app/modules/{captures,ai,reviews}/`, `api/app/jobs/{daily_briefing,weekly_review_draft,ai_cost_rollup}.py`, `api/app/services/review_stats.py` (computes the weekly snapshot from A's, B's, C's tables), `web/src/views/{Capture,WeeklyReview}View.vue`, `web/src/components/CaptureBar.vue` (top-bar input; E mounts it), `web/src/components/home/{Briefing,AiSpend}Widget.vue`, stores and api files for the same.

Rules: every call logs to `ai_calls` with model, tokens, estimated cost (hardcode a price table in `claude_client.py`, update later). Every feature checks its kill switch in Settings `ai_enabled` before calling and returns the deterministic fallback when off. All prompts demand JSON output; parse with a strict schema (pydantic) and reject on failure, falling back rather than crashing. Use `CLAUDE_MODEL_FAST` for classification, `CLAUDE_MODEL_SMART` for the rest. Batch email classification 15 per call. Use prompt caching for the system prompt on classification.

Capture: `POST /api/captures` stores raw text and returns immediately; `POST /api/captures/{id}/process` calls Claude and returns the proposal; `POST /api/captures/{id}/confirm` creates the target record via the owning module's service function (not via HTTP).

Testing: Anthropic client mocked; tests for schema validation, fallback on malformed JSON, kill switch, cost logging. One smoke script `api/scripts/claude_smoke.py` doing a single Haiku call.

Done checklist: all contracts in `docs/AI_CONTRACTS.md` implemented; capture round trip; briefing generated and shown; weekly review draft job produces a row; `ai_calls` visible; `docs/*.md` entries; PROGRESS.md stream D section.

## Stream E — Integration and release

Runs alone on `main` after A, B, C, D are merged. Owns everything the streams were told not to touch.

Tasks in order:

1. Alembic merge migration; `alembic upgrade head` on a fresh DB and on the Railway DB.
2. Wire all routes and nav from `docs/ROUTES.md`; mount `CaptureBar` in `App.vue`; mount `CalendarAccounts` and `MailAccounts` in the Settings view.
3. Assemble `HomeView.vue` from `docs/WIDGETS.md`. Layout: three do's and today's events top, then emails and tasks due, then trackers and hours, then goals and briefing, AI spend bottom.
4. Register every job from `docs/JOBS.md` in `scheduler.py`; start APScheduler in `create_app()` only when `RUN_SCHEDULER=1` (set on Railway, not in tests); guard against double start under gunicorn (`--workers 1`; document that workers must stay at 1 or the scheduler moves to a separate process).
5. Replace any leftover stub in `api/app/services/` with the real implementation; grep for `TODO(stream` and resolve every one.
6. Run the full pytest suite; run all four smoke scripts against real accounts with Wouter present.
7. Add `vite-plugin-pwa` with a manifest and a basic service worker (network-first for `/api`, cache-first for assets). Mobile layout pass: every view usable at 390px width.
8. Deploy. Verify each job runs once on Railway by checking `job_runs`. Update `docs/DEPLOY.md`.
9. Write `docs/PROGRESS.md` final v1 section and `docs/V2.md` with the deferred list from plan section 11 plus anything the streams punted.

Done: Wouter uses Pozzy for a full day with no manual DB edits.

## Reporting

Each stream ends its session by appending to `docs/PROGRESS.md` under its own heading: what is built, what was stubbed, what it needs from another stream, known bugs, how to test it manually. Keep it under 30 lines.
