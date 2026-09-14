# Deploying Pozzy to Railway

Two services from the one GitHub repo (WouterAltepost/Pozzy), Railway project `pozzy`.
This is what was actually done on 2026-09-14. Repeat it for a fresh environment.

Live URLs:
- api: https://api-production-c9d96.up.railway.app (health: `/api/health`)
- web: https://web-production-e418d.up.railway.app

## Prerequisites

- Supabase project with Auth (email + password) and the single user created.
- Railway account linked to GitHub with access to the repo. Railway CLI installed and logged in (`railway whoami`).
- Alembic migration applied to the Supabase database from your machine. Railway has no release step in M1:

```
cd api && source .venv/bin/activate
flask --app app db upgrade
python seeds.py
```

## 1. Create the services (dashboard clicks)

1. Railway dashboard > project `pozzy` > **+ New** (top right) > **GitHub Repo** > `WouterAltepost/Pozzy`.
   If the repo is not listed, click **Configure GitHub App** and grant access first.
2. Click the new service card > **Settings** > rename to `api`.
3. **Settings > Source > Add Root Directory** > `api`. Branch `main`.
4. **Settings > Networking > Public Networking > Generate Domain**. Note the URL.
5. Repeat 1 to 4 for a second service named `web`, root directory `web`.

Build and start need no dashboard config, the repo carries them:
- `api/.python-version` (3.12), `api/requirements.txt`, `api/Procfile`
  (`gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 1 --threads 4`), `api/railway.json` (healthcheck `/api/health`).
- `web/railway.json`: build `npm ci && npm run build`, start `npm start` (`serve -s dist -l $PORT`).

The first deploy of each service fails or crashes because the variables are not set yet. That is expected:
`api` exits with `Missing required environment variables: ...` by design.

## 2. Set variables (CLI, from the local .env)

From the repo root, with `.env` filled in:

```
railway link -p pozzy -e production -s api
set -a && source .env && set +a
railway variables -s api --skip-deploys \
  --set "DATABASE_URL=$DATABASE_URL" \
  --set "SUPABASE_URL=$SUPABASE_URL" \
  --set "SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" \
  --set "SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET" \
  --set "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  --set "TZ=$TZ" \
  --set "FLASK_ENV=production" \
  --set "WEB_ORIGIN=https://<web domain>" \
  --set "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" \
  --set "CLAUDE_MODEL_FAST=$CLAUDE_MODEL_FAST" \
  --set "CLAUDE_MODEL_SMART=$CLAUDE_MODEL_SMART" \
  --set "ICLOUD_USERNAME=$ICLOUD_USERNAME" \
  --set "ICLOUD_APP_PASSWORD=$ICLOUD_APP_PASSWORD" \
  --set "MAIL_ACCOUNTS_JSON=$MAIL_ACCOUNTS_JSON"
railway variables -s web --skip-deploys \
  --set "VITE_SUPABASE_URL=$SUPABASE_URL" \
  --set "VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" \
  --set "VITE_API_BASE=https://<api domain>"
railway redeploy -s api -y
railway redeploy -s web -y
```

`PORT` and `RAILWAY_ENVIRONMENT` are injected by Railway. `FLASK_ENV=production` or `RAILWAY_ENVIRONMENT` stops the API from loading a `.env` file.
Dashboard alternative: service > **Variables** > **Raw Editor**, paste the same `KEY=value` lines.

## 3. Verify

```
curl https://<api domain>/api/health      # {"data":{"status":"ok","db":true,...},"error":null}
curl -i https://<api domain>/api/me       # 401 envelope
railway deployment list -s api            # latest SUCCESS
```

Open the web URL, log in with the Supabase user. Home shows your email, health `connected`, four areas.
Devtools > Network: requests go to the api domain with `Authorization: Bearer` and return 200.

## Gotchas

- `DATABASE_URL` must be the **Transaction pooler** string from Supabase > Connect (host `aws-1-eu-west-1.pooler.supabase.com`, port 6543, user `postgres.<ref>`). The direct host `db.<ref>.supabase.co` is IPv6 only and not reliable from Railway.
- `WEB_ORIGIN` must match the browser origin exactly: scheme + host, no path, no trailing slash. Wrong value shows as CORS errors in the browser while curl still works.
- `VITE_*` values are baked in at build time. Changing them needs a redeploy of `web`.
- Changing the root directory in the dashboard triggers a deploy. Triggering a second build while one is running once failed the web build with `npm error EBUSY ... node_modules/.vite`. Let one build finish, then redeploy.
- Commits that only touch files outside `api/` or `web/` (docs) do not trigger deploys, because of the root directory setting.
- The CLI link is stored per directory. `railway status` shows which project the folder points at; relink with `railway link -p pozzy`.
