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
