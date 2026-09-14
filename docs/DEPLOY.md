# Deploying Pozzy to Railway

Two services from the one GitHub repo (WouterAltepost/Pozzy), Railway project `pozzzy`.
Steps below are filled in click by click as they are performed. Update this file when anything changes.

## Prerequisites

- Supabase project with Auth (email + password) and the user created.
- Railway account linked to GitHub with access to the repo.
- Alembic migration applied to the Supabase database from your machine (Railway has no release step in M1):

```
cd api && source .venv/bin/activate
flask --app app db upgrade
python seeds.py
```

## Service 1: api

1. Railway dashboard > project `pozzzy` > **+ New** > **GitHub Repo** > pick `WouterAltepost/Pozzy`.
2. Open the new service > **Settings** > rename to `api`.
3. **Settings > Source > Root Directory**: `api`. Branch: `main`.
4. Build and start are picked up automatically: `api/.python-version` (3.12), `requirements.txt`, `Procfile`
   (`gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 1 --threads 4`) and `railway.json` (healthcheck `/api/health`).
5. **Variables** tab > **Raw Editor** > paste, with real values:

```
DATABASE_URL=<Supabase transaction pooler URL, port 6543>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon key>
SUPABASE_JWT_SECRET=<legacy JWT secret>
SECRET_KEY=<long random string>
TZ=Europe/Amsterdam
FLASK_ENV=production
WEB_ORIGIN=<web service public URL, filled in after step 2 of the web service>
```

   Optional now, needed in later milestones: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL_FAST`, `CLAUDE_MODEL_SMART`,
   `ICLOUD_USERNAME`, `ICLOUD_APP_PASSWORD`, `MAIL_ACCOUNTS_JSON`. `PORT` is injected by Railway.
6. **Settings > Networking > Public Networking > Generate Domain**. Note the URL, e.g. `https://api-xxxx.up.railway.app`.
7. Wait for the deploy, then open `<api url>/api/health`. Expect `{"data":{"status":"ok","db":true,...},"error":null}`.

## Service 2: web

1. **+ New** > **GitHub Repo** > same repo again.
2. Rename to `web`. **Settings > Source > Root Directory**: `web`.
3. Build and start come from `web/railway.json`: build `npm ci && npm run build`, start `npm start` (`serve -s dist -l $PORT`).
4. **Variables**:

```
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key>
VITE_API_BASE=<api service public URL from step 6 above, no trailing slash>
```

   VITE_* values are baked in at build time, so changing them needs a redeploy.
5. **Settings > Networking > Generate Domain**. Note the URL.
6. Go back to the `api` service > Variables > set `WEB_ORIGIN` to the web URL (no trailing slash). The api redeploys.

## Verify

- Open the web URL, log in with the Supabase user.
- Home page shows your email, health `status ok, db connected`, and the four areas.
- Browser devtools > Network: requests go to the api URL with an `Authorization: Bearer` header and return 200.

## Gotchas

- CORS: `WEB_ORIGIN` must match the browser origin exactly (scheme + host, no path, no trailing slash).
- Supabase Auth > URL Configuration: add the web URL to **Redirect URLs** (only needed for magic links / password reset, not for password login).
