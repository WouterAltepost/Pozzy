# Pozzy progress

## v1 released, 2026-09-14

Live:
- web: https://web-production-e418d.up.railway.app (PWA, installable; service worker network-first for `/api`, cache-first for assets)
- api: https://api-production-c9d96.up.railway.app (`/api/health` reports db and scheduler status)
- Database: Supabase Postgres at Alembic head `e1000000merge` (merge of `b1000000calendar`, `c1000000mail`, `d1000000ai`; all 22 tables from plan section 5 verified by query). Migrations run from a laptop over the pooler URL; Railway has no release step.
- Code: `main` on GitHub WouterAltepost/Pozzy. PRs #1 (A), #2 (B), #3 (C), #4 (D) merged with merge commits; stream E committed directly to main. 207 pytest tests green, `npm run build` green.

Background jobs (APScheduler in the api process, `RUN_SCHEDULER=1` on the Railway api service only, gunicorn `--workers 1`, Europe/Amsterdam):

| Job | Schedule |
|---|---|
| calendar_sync | every 10 min |
| mail_sync_and_classify | every 15 min |
| three_do_rollover | daily 00:05 |
| deadline_urgency | daily 00:10 |
| daily_briefing | daily at Settings `briefing_time` (07:00), read at process start |
| weekly_review_draft | Sunday 18:00 |
| ai_cost_rollup | daily 23:55 |

Verified against real services on 2026-09-14 (local API against Supabase):
- `scripts/claude_smoke.py`: Haiku call ok, 65 in / 37 out, $0.00025 logged to `ai_calls`.
- `scripts/caldav_smoke.py`: 10 iCloud calendars, 31 objects, next 5 events listed with etags.
- `scripts/imap_smoke.py`: 4/4 Gmail accounts log in and list newest subjects.
- Jobs run as functions, each with a `job_runs` row `ok=true`: `calendar_sync` (10/10 calendars, 61 events inserted, 12 s), `mail_sync_and_classify` (355 emails backfilled over 4 accounts, 354 classified by Claude, 1 by rules, 488 s), `daily_briefing` (Claude text written), `three_do_rollover` (0 of 0, nothing pending).
- Every route in ROUTES.md clicked through in Chrome against the local API: no console errors, no failed `/api` calls. Mobile pass at 390px on every view.
- Production job_runs evidence: see the "Production evidence" list below.

Decisions made in integration (BUILD.md task 5):
- Route names and nav order exactly as ROUTES.md after merging A, B, C, D: home, agenda, tasks, goals, mail, trackers, hours, capture, study, notes, review, settings. Unknown paths redirect to home.
- Nav lives in `App.vue` as a second row under the top bar, collapsible behind a menu button under 720px. `CaptureBar` sits between the brand and the user block, authenticated only.
- `HomeView.vue` renders the ten widgets in WIDGETS.md order in a two-column grid from 900px.
- `SettingsView.vue` mounts `CalendarAccounts` (B) and `MailAccounts` (C) inside the Integrations card, replacing A's placeholder divs.
- `settings_defaults.py` keeps every stream's keys; `ai_enabled` gained `three_dos` (D's kill switch) in the defaults, so the Settings page shows six switches without a reseed.
- C's migration chained onto A's (`c1000000mail` revises `a1000000local`), D's too; B's revises M1. The merge migration joins the three heads and changes no schema.
- Job runner: every job keeps its own `run(app)`; `scheduler.py` wraps each in a thread-safe runner with `max_instances=1`, `coalesce=True`, 5 minute misfire grace. Registration is idempotent by job id.

Fixed during integration:
- CalDAV sync failed in production shape with "caldav.icloud.com can't be joined with p55-caldav": `caldav.DAVClient` only moves its base URL during the calendar-home lookup. The client now resolves the home once before any per-calendar request.
- `iso()` looked up the timezone Setting per datetime (400 queries for a 200 row list, 22 s). Cached on `flask.g`; mail list now 1.1 s.
- D's review snapshot test assumed C's Email model was absent.
- Railway web builds failed since the B merge with `EBUSY rmdir node_modules/.vite`: `npm ci` in the build command deleted Railpack's cache mount. Build command is now `npm run build` only.
- Mobile: mail list grid `minmax(0, 1fr)`, goal-add form wraps.

Known gaps: see docs/V2.md. Short version: recurring iCloud occurrences are read-only, the hours timer is browser-local, no thread grouping in Mail, Haiku prompt caching not yet effective, prices hardcoded, no automated browser tests.

Open issues:
- Local login for automated checks was done with an HS256 token minted from `SUPABASE_JWT_SECRET` (the API accepts it as the documented fallback); there is no Supabase user password in `.env`, so a Playwright login flow is not possible without one.
- Calendar selection in Settings currently includes Reminders and Holidays; untick them once so all-day noise stays out of the Agenda.

Production evidence (filled in after the 20 minute wait, see below).

## Stream history

The four stream sections below are the per-stream handover notes from the parallel build (BUILD.md). They are kept for reference; anything they list as "needs from E" is done.

## Stream A (local modules), 2026-09-14

Branch `stream/A-local`, migration `a1000000local` (down_revision M1 `722da3773e5d`, not applied to Supabase; E applies it). 66 pytest tests green (`api/tests/a/`).

Built:
- API: `tasks` (CRUD, quadrant move, complete with hours log, suggest-slot, schedule, unschedule), `dos` (CRUD, suggest, manual rollover), `goals`, `trackers` (CRUD, week grid with completion and streaks, tick, entries, 8 week history), `hours` (CRUD, week summary vs targets), `notes`, `study` (courses, deadlines with auto-created linked task, applications, upcoming feed). Settings GET now merges `settings_defaults.py`; `GET /api/settings/job-runs` and `/defaults` added.
- `scheduling/free_slots.py`: pure free-slot engine, 11 unit tests incl. DST and weekend. Deterministic ranking in `modules/tasks/scheduling.py`; Claude answers are validated against the candidate list.
- Jobs: `three_do_rollover` (00:05), `deadline_urgency` (00:10), both via `jobs/_runner.py` which writes `job_runs`. Listed in `docs/JOBS.md`, not registered in `scheduler.py`.
- Vue: views Tasks (Eisenhower board with native drag and drop, list, edit panel, slot panel), Goals (today and tomorrow do's, suggestions, weekly goals), Trackers (weekly grid, inline SVG line chart), Hours (timer in localStorage, week table), Notes (markdown preview), Study (deadlines, courses, application kanban with drag), Settings (window, targets, kill switches, job runs). Six homepage widgets. Stores and api files per module. `docs/ROUTES.md` and `docs/WIDGETS.md` written.

Stubbed for other streams:
- `services/calendar_read.get_events_between` returns `[]`, `services/calendar_write.{create,update,delete}_event` are no-ops (B replaces, same signatures).
- `integrations/claude_client.rank_slots` and `suggest_dos` return `None` (D implements per `docs/AI_CONTRACTS.md`). Kill switches `ai_enabled.scheduling` and `ai_enabled.three_dos` are honoured by A's callers.
- Settings view has empty mount points for B's `CalendarAccounts` and C's `MailAccounts` (see ROUTES.md).

Decisions: `tags` columns are JSONB arrays, not `text[]`, so SQLite tests work. Deadline tasks use `source="manual"` with `source_ref="deadline:<id>"` because the plan's source enum has no deadline value. Hours logging on task completion is idempotent per task (one log row, updated on re-complete). Trackers store one entry per tracker per day; weekly_count ticks increment that day's value.

Known gaps and how to test:
- Vue views are compile-checked (all SFCs build) but not clicked through, because routes are wired by E. To test manually before merge: add the ROUTES.md entries to the router, run `flask --app app run --debug` and `npm run dev`, apply the migration with `flask db upgrade a1000000local` on the direct DB host.
- The hours timer lives in the browser (localStorage), not the API. A server-side timer can come later if the Telegram bot needs it.
- Task quick-add does not yet offer Claude parsing (that is D's capture flow).

## Stream B (calendar), 2026-09-14

Branch `stream/B-calendar`, migration `b1000000calendar` (down_revision M1 `722da3773e5d`, not applied to Supabase; E applies it). 42 pytest tests green under `api/tests/b/`, 108 in total after the rebase on A.

Built:
- `integrations/caldav_client.py`: pure `parse_occurrences` (local recurrence expansion with `recurring-ical-events`, RRULE/RDATE/EXDATE/RECURRENCE-ID overrides, all-day, DST, DURATION) and `build_ics` (single VEVENT with `X-POZZY-TASK-ID`), plus `CalDAVClient` (list, fetch with etags, create/update/delete by UID, 3 attempts with backoff on 5xx). Smoke script `api/scripts/caldav_smoke.py` ran against the real account: 10 calendars, 31 objects parsed, etags present. `--write` does a create/read/delete round trip, not yet run.
- Models `CalendarAccount` (bootstrapped from `ICLOUD_*` env on first use, calendar selection, write calendar, cached discovery, last sync status) and `CalendarEvent` (one row per occurrence, unique on calendar_url+uid+recurrence_id, UTC).
- `modules/calendar/service.py` + `jobs/calendar_sync.py` (every 10 min, `docs/JOBS.md`): window from Settings `calendar_sync_days_back/forward` (7/30), per-calendar commit, etag skip, stale occurrence deletion, one failing calendar marks the run failed but the others still land. Moved Pozzy events (`X-POZZY-TASK-ID`) push their new times back onto the task.
- `services/calendar_read.get_events_between` and `calendar_write.{create,update,delete}_event` replace A's stubs with the same signatures. A's tests still pass unchanged; `POST /api/tasks/{id}/schedule` now creates the iCloud event end to end (tested with the fake client).
- API `/api/calendar/*`: events in range (plus scheduled tasks), create/update/delete single events (iCloud first, then local mirror), sync now, account get/put/discover.
- Vue: `AgendaView` (week and day grid, click empty space to create, click event to edit/delete, side panel form, sync bar), `TodayEventsWidget`, `settings/CalendarAccounts` (select calendars, choose write calendar, discover, sync now). `docs/ROUTES.md` and `docs/WIDGETS.md` updated.

Decisions:
- Recurrence is expanded locally, not by the server. iCloud server-side expansion drops overrides. The expander stamps RECURRENCE-ID on single events too, so "recurring" is decided from the source VEVENTs.
- `get_events_between` excludes all-day events (deadlines and birthdays must not block a whole working day) and task-linked events (A already passes scheduled tasks, counting them twice would block a task's own slot on reschedule).
- Occurrences of recurring events are read-only in Pozzy (409 `recurring_not_editable`). Writing overrides into a master VEVENT is v2.
- The account row stores `secret_ref` (env var name), never the password.

Needs from other streams: nothing. E must register `calendar_sync` in the scheduler, wire `/agenda`, mount `CalendarAccounts`, and apply the migration.

Known gaps and how to test:
- Vue views are compile-checked, not clicked through (routes are wired by E). To test manually: add the ROUTES.md row to the router, apply the migration, run the API and `npm run dev`, open Settings, click Discover calendars, untick Reminders and Holidays, save, then Sync now. The Agenda should show the synced week.
- Wouter verifies the iPhone round trip: create an event in the Agenda, check it on the phone, move it on the phone, Sync now, check the Agenda. Then delete it from the Agenda. Or run `python scripts/caldav_smoke.py --write --calendar Taken` for a scripted version.
- Manual `POST /api/calendar/sync` runs synchronously and does not write a `job_runs` row; only the scheduled job does.
- Events created in the Agenda get `etag` null until the next sync fills it. Harmless: the next sync treats them as changed once.

## Stream C (mail), 2026-09-14

Branch `stream/C-mail`, migration `c1000000mail` (down_revision `a1000000local`, not applied to Supabase; E applies it). 103 pytest tests green, 37 of them in `api/tests/c/`. New dependency `imap-tools`.

Built:
- `integrations/imap_client.py`: read-only IMAP (imap-tools, `imap.gmail.com`, INBOX only, BODY.PEEK, no STORE/COPY/MOVE/EXPUNGE anywhere). UID incremental fetch, 7 day backfill on first run, per-run cap (`mail_max_per_sync`, 500) that drains a backlog over several runs, 2 KB snippet from text/plain with stripped-html fallback, attachments flagged but never downloaded, best effort `X-GM-LABELS`.
- Models `MailAccount`, `Email`. Accounts are upserted by email from `MAIL_ACCOUNTS_JSON` on every sync and on `GET /api/mail/accounts`; passwords stay in the env (`secret_ref = env:<email>`). Emails are unique on `(account_id, uid)`; manual overrides live in `priority_override`, `category_override`, `area_override_id` and classification never writes them.
- `jobs/mail_sync.py` (`mail_sync_and_classify`, `*/15`, listed in JOBS.md): sync every enabled account, one failing account is recorded on `mail_accounts.last_error` and does not stop the others; then classify. Job fails only when every account fails.
- `services/mail_classify.py`: batches of 15, calls `claude_client.classify_emails` via `getattr` (D adds the function; `claude_client.py` was not edited to avoid a merge conflict), validates each item against the contract in `docs/AI_CONTRACTS.md` (Stream C), rule fallback for everything else. Rules: notification and newsletter get priority 4, finance/school/client/personal by sender and subject heuristics, area from category, `needs_reply` false.
- API `/api/mail`: `emails` (filters account, category, area, needs_reply, handled, priority, q; sorted effective priority then date), `emails/<id>` (with snippet and linked task id), `PATCH` overrides and handled, `emails/<id>/task` (A's `tasks.service.create_task`, `source=email`, `source_ref=<email id>`, idempotent), `emails/<id>/reclassify`, `top`, `counts`, `accounts` (+ `PATCH`, `test`), `sync`.
- Vue: `MailView.vue` (filters, rows with account colour and priority badge, detail panel with snippet, Gmail link from `message_id`, mark handled, overrides, create task), `components/mail/*`, `stores/mail.js`, `api/mail.js`, `home/TopEmailsWidget.vue`, `settings/MailAccounts.vue`. All SFCs compile; not clicked through because routes are wired by E. ROUTES.md (order 5) and WIDGETS.md (order 3) updated.

Verified against the real accounts: `scripts/imap_smoke.py` logs in to all four and lists the newest subjects. A full job run into a scratch SQLite DB synced 94 emails from the four accounts, a second run added only the new ones, all classified by rules. The Work address in `.env` is complete (`wout@alpacaai.nl`); the M1 open issue about it was a display artefact.

Needs from other streams: D implements `classify_emails` (contract written). E wires the route, widget, `MailAccounts` mount, and registers the job.

Known gaps and how to test:
- Sync speed is roughly 1 s per message on Gmail plus a few seconds login per account; the first 7 day backfill on a busy inbox runs over a few job cycles because of the 500 cap. Fine for a 15 min job.
- Gmail labels are only present on messages that have one beyond INBOX (`\Important`, user labels). `\Inbox` itself is omitted by Gmail.
- Manual test before merge: add the ROUTES.md row to the router, mount `MailAccounts`, `flask db upgrade c1000000mail`, then `POST /api/mail/sync` or the Settings "Sync now" button.

## Stream D (AI), 2026-09-14

Branch `stream/D-ai`, migration `d1000000ai` (down_revision `a1000000local`; tables `captures`, `daily_briefings`, `weekly_reviews`). 122 pytest tests green (`api/tests/d/` has 56). Smoke script `api/scripts/claude_smoke.py` ran against the real key: Haiku, 65 in / 32 out, $0.000225. Every prompt was also exercised once against the live models (11 calls, about 5 cents) and returned valid JSON.

Built:
- `integrations/claude_client.py`: one `_call` helper (kill switch from Settings `ai_enabled.<switch>` merged over defaults, model per tier from `CLAUDE_MODEL_FAST/SMART`, prompt file, JSON parse tolerant of fences, pydantic validation, `ai_calls` row with tokens and cost from a hardcoded `PRICES` table, never raises). Contracts: `rank_slots`, `suggest_dos` (A), `classify_emails` (C), plus D's `parse_capture`, `write_briefing`, `review_week`, `ping`. Under `TESTING` no real client is ever built.
- Prompts in `api/app/prompts/*.md` (only `api/` deploys to Railway); `docs/prompts/` holds symlinks to them. Each file documents feature, switch, model and the JSON schema above `## System` and `## User`.
- Capture: `POST /api/captures` stores at once, `/process` proposes (Claude or `parse_deterministic`: prefixes note:/goal:/event:, tracker names, relative dates, hashtags, area words), `/confirm` creates via A's services (`type` and `fields` may override the proposal; pydantic-validated), `/discard`. Event captures become scheduled tasks through A's `schedule_task` (reaches iCloud once B is merged). `CaptureView.vue`, `CaptureBar.vue`, `ProposalEditor.vue`, store, api.
- Briefing: `modules/ai/briefing.py` builds context from A's tables (B's events and C's emails via guarded imports), Claude text or deterministic text, one `daily_briefings` row per day. `GET/POST /api/ai/briefing`, `GET /api/ai/briefing/context`, job `daily_briefing`, `BriefingWidget.vue`.
- Weekly review: `services/review_stats.py::compute(week)` snapshot; `modules/reviews/` draft (Claude reflection and next-week focus, deterministic fallback), notes and focus edits, `finalize` creates next week's `weekly_goals` via A's goals service (idempotent on title). Job `weekly_review_draft`. `WeeklyReviewView.vue`.
- Spend: `GET /api/ai/spend` (month vs Settings `ai_monthly_budget_usd`, today, 7 days, per feature and model, recent calls), job `ai_cost_rollup` into Settings `ai_spend_daily`, `AiSpendWidget.vue`.
- Docs: `AI_CONTRACTS.md` (Stream D section), `JOBS.md` (3 jobs), `ROUTES.md` (orders 8 and 11, CaptureBar mount note), `WIDGETS.md` (rows 9 and 10).

Needs from other streams / E:
- C's contract was read from the local `pozzy-C` worktree (unpushed). E merges C's AI_CONTRACTS section; the implementation matches it exactly.
- Blueprints `captures`, `ai`, `reviews` are registered in `app/__init__.py` and models in `models/__init__.py` (merge conflicts with B and C expected there, trivial).
- Register the three jobs from JOBS.md; `daily_briefing` should read `briefing_time` from Settings.
- `anthropic` and `pydantic` added to `api/requirements.txt`; Railway installs them on the next api deploy.

Known gaps and how to test:
- Views are compile-checked (Vite) but not clicked through, routes are wired by E. Manual test after E wires routes: type "call dentist tomorrow" in the top bar, confirm, check Tasks; open `/review`, Generate, edit focus, Finalize, check next week's Goals; Home shows Briefing and AI spend.
- `_call` commits the SQLAlchemy session when it logs; callers must not hold uncommitted work they want rolled back (A's and D's callers do not).
- Haiku 4.5 prompt caching needs a 4096-token prefix; the classify system prompt is well under that, so cache reads stay 0 until it grows. Harmless.
- Prices are the September 2026 list rates; update `PRICES` in `claude_client.py` when Anthropic changes them or when `.env` switches to `claude-sonnet-5`.
