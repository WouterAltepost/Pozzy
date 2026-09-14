# Milestone 1 — Scaffold, auth end to end, deploy

Read `CLAUDE.md` and `docs/POZZY_PLAN.md` (sections 2, 3, 5, 9) first. This milestone builds no product features. It is done when a logged-in user sees a "Pozzy" page served from Railway that displays their email and a live health check from the API, and Alembic has created the first tables.

## Deliverables

### 1. Repo structure

```
api/
  app/
    __init__.py        create_app() factory
    config.py          reads env vars, fails loudly on missing required ones
    extensions.py      db (SQLAlchemy), migrate (Alembic via Flask-Migrate), scheduler (APScheduler, not started in M1)
    auth.py            require_auth decorator: validates Supabase JWT (HS256, SUPABASE_JWT_SECRET, audience "authenticated"), puts user id + email on flask.g
    models/
      __init__.py
      base.py          BaseModel mixin: id uuid pk, created_at, updated_at
      area.py          Area
      setting.py       Setting (key, value jsonb)
      job_run.py       JobRun
      ai_call.py       AiCall
    modules/
      health/routes.py GET /api/health -> {data:{status:"ok", db:true|false, time:iso}}
      me/routes.py     GET /api/me -> {data:{id, email}} (requires auth)
      settings/routes.py GET/PUT /api/settings (requires auth)
      areas/routes.py  GET /api/areas (requires auth)
    errors.py          JSON error handlers, response envelope helpers
  migrations/          Alembic
  seeds.py             seeds the four areas and default settings (idempotent)
  tests/
    test_auth.py       valid token passes, missing/invalid/expired token -> 401
    test_health.py
  requirements.txt
  Procfile             web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 1 --threads 4
  railway.json         (optional) healthcheckPath /api/health
  .env.example         (copy of the root one, or symlink; Railway uses service vars anyway)
web/
  index.html
  vite.config.js       dev proxy /api -> http://localhost:5000
  package.json
  src/
    main.js
    App.vue            top bar with "Pozzy", user email, logout; <router-view/>
    router/index.js    routes: /login (public), / (guarded)
    lib/supabase.js    createClient(VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
    lib/api.js         fetch wrapper: adds Bearer token from supabase session, unwraps {data,error}, throws on error
    stores/auth.js     Pinia: session, user, login(email,pw), logout(), init() (restores session)
    views/LoginView.vue
    views/HomeView.vue shows /api/me result and /api/health result, and the list from /api/areas
  .env.example         VITE_SUPABASE_URL=, VITE_SUPABASE_ANON_KEY=, VITE_API_BASE=
```

### 2. Config and secrets

`api/app/config.py` must read: DATABASE_URL, SUPABASE_URL, SUPABASE_JWT_SECRET, SECRET_KEY, TZ. Required in every env. Everything else in the root `.env.example` (ANTHROPIC_API_KEY, ICLOUD_*, MAIL_ACCOUNTS_JSON, CLAUDE_MODEL_*) is optional in M1 and must not be validated yet, only read into config with None defaults.

Local dev: Flask loads `../.env` from the repo root via python-dotenv so there is one `.env` for the whole project. Never load it in production (Railway injects vars). Do not create a second `.env` in `api/`.

Frontend env: `web/.env.local` (gitignored) with the two VITE_SUPABASE_* values and `VITE_API_BASE=` (empty locally because of the Vite proxy; on Railway it is the api service's public URL).

### 3. Auth

Supabase Auth issues HS256 JWTs signed with SUPABASE_JWT_SECRET. `require_auth`: read `Authorization: Bearer <jwt>`, decode with PyJWT, verify signature, exp, and `aud == "authenticated"`. On failure return 401 with the envelope. Store `sub` and `email` on `flask.g.user`. CORS: allow the web origin only (env `WEB_ORIGIN`, default http://localhost:5173), with Authorization header.

Note: if the Supabase project uses the newer asymmetric JWT signing (ES256/RS256) instead of the legacy HS256 secret, verify via the project's JWKS at `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` instead. Check which one this project uses by decoding a real token header, and implement that one. Report which it was.

### 4. Database

SQLAlchemy 2 style models. `BaseModel` mixin with `id UUID default uuid4`, `created_at`, `updated_at` (server defaults, `onupdate`). Tables in M1: `areas`, `settings`, `job_runs`, `ai_calls`. Nothing else yet. One Alembic migration. `python seeds.py` inserts Study, Work, Personal, Health with colours and sort order, and default settings: `working_window` `{"days":[1,2,3,4,5],"start":"08:00","end":"18:00"}`, `timezone` `"Europe/Amsterdam"`, `week_start` `1`, `ai_enabled` `{"mail_classify":true,"briefing":true,"scheduling":true,"capture":true,"weekly_review":true}`, `hour_targets` `{"Work":960}` (minutes per week).

Use the Supabase transaction pooler URL (port 6543) with `pool_pre_ping=True`. Alembic migrations should run against the same URL; if the pooler rejects DDL in transaction mode, use the session pooler (port 5432) URL for migrations only and document it in PROGRESS.md.

### 5. Deploy

Railway project "pozzy", two services from the GitHub repo:
- `api`: root directory `api`, start via Procfile, variables from the root `.env.example` list plus `WEB_ORIGIN` = the web service's public URL, `PORT` provided by Railway.
- `web`: root directory `web`, build `npm ci && npm run build`, serve `dist/` with a tiny static server (`serve -s dist -l $PORT`) or Railway's static preset. Variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE` = api service public URL.

Write the exact click-by-click Railway steps into `docs/DEPLOY.md` as you do them, including where root directory and variables are set, so it is reproducible.

### 6. Tests

`pytest` in `api/`: auth decorator (valid, missing, expired, wrong secret), health endpoint, settings round trip. Use a SQLite in-memory DB for tests if UUID/JSONB types allow it; otherwise a Postgres test schema. State which.

### 7. Definition of done

- `flask run` + `npm run dev` locally: login with the Supabase user, home page shows email, health ok, four areas.
- Same on the Railway URLs.
- `pytest` green.
- `docs/PROGRESS.md` updated: active milestone 2, what is deployed, the JWT algorithm found, the pooler port used for migrations, any gotchas.
- No secrets in git (`git log -p | grep -E 'sk-ant|eyJ'` returns nothing).

## Do not

- Do not add vite-plugin-pwa, Tailwind, or any UI library. Plain CSS, minimal.
- Do not start APScheduler. Only wire the extension.
- Do not create tables beyond the four listed.
- Do not touch the Supabase JS client for anything except auth.
