# Pozzy progress

Active milestone: 1 (scaffold, auth end to end, deploy). Brief: docs/briefs/M1-scaffold.md
Status: code complete and verified locally, Railway deploy pending (done together with Wouter, see docs/DEPLOY.md).

## Done
- 2026-09-14: plan written (docs/POZZY_PLAN.md), CLAUDE.md, .env.example.
- 2026-09-14: milestone 0 complete. Supabase project, Anthropic key, Apple app-specific password, 4 Google app passwords, Railway project (`pozzzy`), GitHub repo (WouterAltepost/Pozzy). All secrets in root .env (gitignored).
- 2026-09-14: M1 scaffold. `api/` Flask 3 app factory, config with loud failure on missing vars, JWT auth, models Area/Setting/JobRun/AiCall, blueprints health/me/settings/areas, Alembic migration 722da3773e5d applied to Supabase, idempotent `seeds.py` run. `web/` Vue 3 + Vite + Pinia + Router, Supabase JS for auth only, login and home views. 16 pytest tests green.

## Facts found in M1
- JWT algorithm: **ES256** (asymmetric). The project JWKS at `/auth/v1/.well-known/jwks.json` publishes a P-256 key. `require_auth` verifies via JWKS (cached per process) and falls back to HS256 with `SUPABASE_JWT_SECRET` when a token header says HS256. To be confirmed against a real access token on first login.
- Tests use SQLite in-memory. `sqlalchemy.Uuid` and `JSON().with_variant(JSONB, "postgresql")` work on SQLite, so no Postgres test schema was needed.
- Pooler: the `aws-0-eu-central-1` transaction pooler host in the original DATABASE_URL rejects the tenant ("tenant/user not found"), so the project is on a different pooler host. Migration and seed ran over the **direct host** `db.<ref>.supabase.co:5432` (works locally over IPv6). Railway needs the correct pooler URL from Supabase > Connect > Transaction pooler; update `.env` too.
- Vite dev proxy targets `127.0.0.1:5000`, not `localhost`, because Node resolves localhost to IPv6 and Flask listens on IPv4.

## Next
- Wouter: log in locally (http://127.0.0.1:5173) to confirm ES256 tokens verify and the home page shows email, health, four areas.
- Deploy `api` and `web` on Railway following docs/DEPLOY.md, then set active milestone to 2.

## Open issues
- Work mail address in .env reads `wout@alpacaai`, looks truncated (matters from milestone 6).

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
