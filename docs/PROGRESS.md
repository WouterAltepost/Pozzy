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
