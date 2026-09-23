# CLAUDE.md — Pozzy (Personal Operating System)

Read `docs/POZZY_PLAN.md` before doing anything. It is the source of truth for scope, data model, integrations, and build order. If a request conflicts with the plan, say so and ask before deviating.

## Who you are working with

Wouter, solo developer, thinks in systems and workflows, intermediate coder. He directs, you write the code. Explain decisions briefly, do not over-explain basics. Never use long dashes in prose or comments. Be direct about problems; do not sugarcoat.

## Project

Single-user personal dashboard. Modules: Homepage, Agenda (iCloud CalDAV read/write), Mail (IMAP read-only, 4 Google accounts, Haiku classification), Tasks (Eisenhower + due date + Claude slot suggestions), Goals (weekly goals + daily three do's with rollover), Tracking (habits), Hours (time per area), Capture (NL quick inbox), Study, Notes, Weekly Review, Settings.

Life areas: Study, Work, Personal, Health. Timezone Europe/Amsterdam. Week starts Monday. UI in English.

## Stack

- `api/` Flask 3, SQLAlchemy 2, Alembic, APScheduler, `caldav`, `imap-tools`, `anthropic`. Python 3.12. Gunicorn on Railway.
- `web/` Vue 3 (Composition API, `<script setup>`), Vite, Vue Router, Pinia, vite-plugin-pwa (added at milestone 9, not before). Plain CSS or a light utility setup; no design work in v1.
- Supabase: Postgres (via `DATABASE_URL`, SQLAlchemy only, no Supabase JS data access) and Auth (email + password, single account).
- Railway: two services from this monorepo (`api`, `web`).

## Hard rules

1. Every module must work with AI and integrations switched off. Never make a page depend on a Claude call or an external sync to render.
2. All business logic lives in Flask. Vue only calls `/api/*`. Vue never holds the Supabase service key or `DATABASE_URL`.
3. Every `/api/*` route validates the Supabase JWT (`Authorization: Bearer`). No unauthenticated routes except `/api/health`.
4. Secrets only via environment variables. Never commit `.env`. `.env.example` lists every variable with a placeholder.
5. Background jobs are idempotent and log to `job_runs`. A job failure must never crash the web process.
6. Every Anthropic call goes through `api/app/integrations/claude_client.py`, uses a named prompt template from `docs/prompts/`, and writes a row to `ai_calls`. Each AI feature has a kill switch in Settings.
7. Scheduling: free slots are computed deterministically in Python. Claude only ranks candidates it is given. Never let Claude invent a slot.
8. Mail is read-only. The IMAP client never issues STORE, COPY, MOVE, EXPUNGE or any flag change.
9. Schema changes go through Alembic migrations. Never edit the DB by hand.
10. Follow the build order in plan section 9. Finish and deploy a milestone before starting the next one.
11. Every migration that creates a table ends with `op.execute("ALTER TABLE <name> ENABLE ROW LEVEL SECURITY")`. The `anon` and `authenticated` roles hold no grants in `public` (migration `i1000000rls`); Vue never reads the database through Supabase.

## Conventions

- Flask app factory in `api/app/__init__.py`. One blueprint per module under `api/app/modules/<name>/` containing `models.py`, `schemas.py`, `routes.py`, `service.py`.
- Jobs under `api/app/jobs/`, registered in `api/app/scheduler.py`.
- Integrations under `api/app/integrations/`.
- JSON responses: `{ "data": ..., "error": null }` or `{ "data": null, "error": { "code", "message" } }`.
- Dates in API: ISO 8601 with timezone. Store UTC in Postgres, convert in the API layer using the timezone from Settings.
- Vue: one route per module under `web/src/views/`, shared components under `web/src/components/`, one Pinia store per module, API calls in `web/src/api/<module>.js`.
- Tests: `pytest` for the API, at minimum for the free-slot engine, three-do rollover, and email classification parsing. Run `pytest` before declaring a milestone done.

## Local development

```
cd api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env   # fill in
flask --app app run --debug
cd web && npm install && npm run dev
```

## Session workflow

Start each session by reading `docs/POZZY_PLAN.md` section 9 and `docs/PROGRESS.md` to see which milestone is active. Update `docs/PROGRESS.md` at the end of every session: what was done, what is deployed, what is next, any open issue. Keep it short.
