# Pozzy progress

Active milestone: 2 (Areas, Settings, Tasks, Goals). Milestone 1 is deployed and verified.

## Deployed
- api: https://api-production-c9d96.up.railway.app (Railway project `pozzy`, service `api`, root `api`)
- web: https://web-production-e418d.up.railway.app (service `web`, root `web`)
- Database: Supabase Postgres, Alembic head 722da3773e5d, seeds applied. Migrations run from a laptop, see docs/DEPLOY.md.

## Done
- 2026-09-14: plan written (docs/POZZY_PLAN.md), CLAUDE.md, .env.example.
- 2026-09-14: milestone 0 complete. Supabase project, Anthropic key, Apple app-specific password, 4 Google app passwords, Railway project, GitHub repo (WouterAltepost/Pozzy). All secrets in root .env (gitignored).
- 2026-09-14: milestone 1 complete. `api/` Flask 3 app factory, config that fails loudly on missing vars, Supabase JWT auth, models Area/Setting/JobRun/AiCall, blueprints health/me/settings/areas, one Alembic migration, idempotent `seeds.py`, 16 pytest tests. `web/` Vue 3 + Vite + Pinia + Router, Supabase JS for auth only, login and home views. Login verified locally and on Railway. Deploy steps in docs/DEPLOY.md.

## Facts found in M1
- JWT algorithm: **ES256** (asymmetric), confirmed with a real login. The project JWKS at `/auth/v1/.well-known/jwks.json` publishes a P-256 key. `require_auth` verifies via JWKS (cached per process) and falls back to HS256 with `SUPABASE_JWT_SECRET` when a token header says HS256.
- Tests use SQLite in-memory. `sqlalchemy.Uuid` and `JSON().with_variant(JSONB, "postgresql")` work on SQLite, so no Postgres test schema was needed.
- Pooler: the project lives on `aws-1-eu-west-1.pooler.supabase.com`, not `aws-0-eu-central-1` as first assumed. Transaction pooler (port 6543) is used for the app and for Alembic; `flask db upgrade` and `db current` both worked through it. The first migration itself was applied over the direct host before the pooler host was known. If a future DDL migration fails on 6543, switch to the session pooler (5432) for that run and note it here.
- Vite dev proxy targets `127.0.0.1:5000`, not `localhost`, because Node resolves localhost to IPv6 and Flask listens on IPv4.
- Railway variables were set with the CLI from the local `.env`, so no secret went through the dashboard or chat.

## Next
- Milestone 2 per plan section 9: Areas (edit), Settings page, Tasks CRUD + Eisenhower board, Goals (weekly goals, three do's, rollover job). Write the brief first: docs/briefs/M2-core.md.

## Open issues
- Work mail address in .env reads `wout@alpacaai`, looks truncated (matters from milestone 6).
- APScheduler is wired but not started. Starts in M2 with the rollover job.

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
