# Pozzy (Personal Operating System) — v1 Plan

Status: planning complete, ready to build. Last updated 2026-09-14.

Owner: Wouter Altepost. Built with Claude Code. Deployed on Railway.

## 1. What Pozzy is

A single private web app that holds everything Wouter needs to run his week: calendar, mail triage, tasks, daily and weekly goals, habit tracking, hours per life area, study deadlines, quick capture, and a weekly review. Claude is used where judgement is needed (email priority, scheduling suggestions, daily briefing, natural-language input, weekly reflection), not for plain CRUD.

Design principle for v1: every module must be usable with zero AI and zero integrations. AI and integrations enrich the data; they are never required to open a page. If Gmail is down, Tasks still work.

## 2. Decisions locked

| Topic | Decision |
|---|---|
| Backend | Flask (REST API) + APScheduler for background jobs, one Railway service |
| Frontend | Vue 3 + Vite + vite-plugin-pwa (PWA is a later config step, not a rewrite), one Railway service |
| Database | Supabase Postgres, accessed from Flask via SQLAlchemy (not via Supabase client) |
| Auth | Supabase Auth, single account, email + password. Vue gets a JWT, Flask validates it on every request |
| Calendar | iCloud via CalDAV, read + write, Apple app-specific password |
| Mail | 3 Gmail + 1 Google Workspace, read only, via IMAP with app passwords (see 4.2 for why not the Gmail API) |
| AI | Anthropic SDK. Haiku for high-volume classification, Sonnet for briefing, scheduling, weekly reflection, NL input |
| Task priority | Eisenhower matrix (urgent x important) + due date |
| Scheduling window | 08:00–18:00 Mon–Fri default, editable in Settings, minus calendar events |
| Three do's | Set evening before or morning; unfinished ones roll over automatically |
| Life areas | Study, Work (alpaca AI, UDefine, others), Personal (Trading, Investing, Learning), Health |
| Locale | Europe/Amsterdam, week starts Monday, UI in English |
| Mail sync | Backfill 7 days once, then poll every 15 min, classify new mail with Haiku |
| Build | Everything in one v1, in the milestone order in section 9 |
| Later | Mobile PWA polish, Telegram bot for input and notifications |

## 3. Architecture

```
Browser (Vue 3 SPA, PWA-ready)
   |  HTTPS, Bearer JWT (Supabase Auth)
   v
Flask API (Railway service "pozzy-api")
   |-- /api/* REST endpoints, one blueprint per module
   |-- APScheduler (in-process):
   |     calendar sync, mail sync + classify, three-do rollover,
   |     tracker week reset, daily briefing, weekly review draft
   |-- integrations/
   |     caldav_client.py   (iCloud)
   |     imap_client.py     (Gmail / Workspace)
   |     claude_client.py   (Anthropic SDK, prompt templates)
   v
Supabase Postgres (+ Supabase Auth)
```

Repo layout (monorepo):

```
pozzy/
  api/          Flask app, SQLAlchemy models, Alembic migrations, jobs, integrations
  web/          Vue 3 app
  docs/         this plan, ADRs, prompt templates
  CLAUDE.md     conventions for Claude Code sessions
```

Railway: two services from one repo using root directory settings. Env vars listed in section 10.

Why SQLAlchemy over the Supabase client from Vue: all logic (rollover, scheduling, classification) lives in one place, and the frontend never needs the service key. Supabase is used as managed Postgres + Auth, nothing more, so it can be swapped for Railway Postgres later if wanted.

## 4. Integrations

### 4.1 iCloud calendar (CalDAV)

Library: `caldav` (Python). Auth: Apple ID + app-specific password from appleid.apple.com. Discovery via `https://caldav.icloud.com` principal URL; the library resolves the calendar home. Store the chosen calendar URLs in Settings.

Sync job (every 10 min): fetch events in window [today − 7d, today + 30d], upsert into `calendar_events` keyed on the CalDAV UID. Delete rows whose UID no longer appears in the window. Keep `etag` to skip unchanged events.

Write: when a scheduling suggestion is accepted, create a VEVENT on the chosen calendar with the task title, store the UID on the task, and mark the task `scheduled`. Editing or deleting the event from Pozzy updates the VEVENT. Editing it from the iPhone is picked up by the next sync.

Known limits: iCloud CalDAV occasionally returns 5xx; the job must retry with backoff and never fail the whole sync on one calendar.

### 4.2 Mail (IMAP, not Gmail API)

Why IMAP: Google OAuth apps in "Testing" status issue refresh tokens that expire every 7 days, and `gmail.readonly` is a restricted scope that formally requires app verification for external production apps. For a one-person tool that is repeated re-authorisation or a verification process for nothing. IMAP with a per-account app password (requires 2-step verification on each Google account) gives read access with no OAuth at all, works the same for the Workspace account, and the read-only scope is enforced by simply never issuing write commands. If richer features (labels, threads, actions) are wanted in v2, the Gmail API can be added then.

Library: `imap-tools`. Per account: host `imap.gmail.com`, SSL, app password from env or encrypted Settings row.

Sync job (every 15 min): for each account, fetch messages with UID greater than the last seen UID (INBOX only for v1; All Mail is too noisy). Store headers, snippet (first ~2 KB of text body), and Gmail labels if exposed via `X-GM-LABELS`. Never download attachments.

Classification (Haiku, batched 10–20 emails per call): output JSON with `priority` (1 urgent, 2 important, 3 normal, 4 low/noise), `category` (client, school, finance, personal, newsletter, notification, other), `area` (one of the four life areas or null), `needs_reply` (bool), `one_line_summary`. Store on the email row. Manual overrides are stored in separate columns so re-classification never clobbers them.

Unified inbox view: all accounts merged, sorted by priority then date, filter by account, category, area, needs_reply. Marking as "handled" in Pozzy is local only (no IMAP flag changes in v1).

### 4.3 Claude

One `claude_client.py` with named prompt templates under `docs/prompts/`. Every call logs model, input tokens, output tokens and cost estimate to `ai_calls` so spending is visible on the homepage. Each feature has a kill switch in Settings.

| Feature | Model | Trigger | Rough cost |
|---|---|---|---|
| Email classify | Haiku | every 15 min, only new mail | cents per day |
| Daily briefing | Sonnet | 07:00 daily job | 1 call/day |
| Scheduling suggestion | Sonnet | on demand per task | 1 call/request |
| NL quick capture | Sonnet | on submit | 1 call/entry |
| Weekly reflection | Sonnet | Sunday 18:00 job | 1 call/week |

Scheduling note: the free-slot computation is deterministic Python (working window minus events minus already scheduled tasks, honouring estimated duration). Claude only picks among the candidate slots and explains why, so a bad model answer can never produce an impossible slot.

## 5. Data model (Postgres)

All tables have `id` (uuid), `created_at`, `updated_at`. Single user, so no `user_id` in v1, but Supabase Auth's user id is stored in Settings for future RLS.

**areas**: name, color, sort_order. Seeded with Study, Work, Personal, Health. Sub-tags (UDefine, Trading) live in a `tags` text[] on tasks/hours rather than a nested area table.

**tasks**: title, description, area_id, tags[], urgent (bool), important (bool), status (inbox, todo, scheduled, done, dropped), due_date, estimated_minutes, scheduled_start, scheduled_end, calendar_uid, completed_at, source (manual, capture, email, three_do), source_ref.

**daily_dos**: date, task_id (nullable, a do can be free text), title, done (bool), rolled_from_date (nullable), position 1–3+.

**weekly_goals**: week_start (Monday date), title, area_id, target_value (nullable), current_value, done, notes.

**trackers**: name, area_id, type (daily_bool, weekly_count, numeric, duration), target_value, target_period (day, week), unit, active, sort_order. Examples: creatine (daily_bool), vitamins (weekly_count, target 2–3), sauna (weekly_count, target 1), weight (numeric), sleep (numeric).

**tracker_entries**: tracker_id, date, value (numeric; 1/0 for bool), note.

**hours_logs**: date, area_id, tags[], minutes, note, task_id (nullable). Weekly view sums per area; a target per area (e.g. Work 16h) lives in Settings.

**calendar_accounts**: name, caldav_url, username, secret_ref, calendar_urls[], enabled.

**calendar_events**: account_id, uid, etag, title, start, end, all_day, location, description, calendar_url, last_synced_at.

**mail_accounts**: label, email, imap_host, secret_ref, last_uid, enabled, color.

**emails**: account_id, uid, message_id, thread_hint, from_name, from_email, to, subject, date, snippet, labels[], priority, category, area_id, needs_reply, summary, priority_override, category_override, handled (bool), handled_at.

**captures**: raw_text, status (new, processed, discarded), parsed_type (task, event, goal, note, tracker), parsed_json, result_ref, processed_at.

**notes**: title, body (markdown), area_id, tags[], pinned.

**courses**: name, code, period, ects, status. **deadlines**: course_id, title, due_at, type (assignment, exam, presentation), done, task_id (nullable, auto-created task). **applications**: company, role, status (found, applied, interview, offer, rejected), applied_at, next_step, next_step_date, notes, link.

**weekly_reviews**: week_start, stats_json (computed snapshot), reflection (Claude), notes (Wouter), next_week_focus, finalized.

**settings**: key/value (working window, timezone, hour targets per area, AI kill switches, briefing time).

**ai_calls**: feature, model, input_tokens, output_tokens, cost_estimate, ok, error, created_at.

## 6. Modules

### 6.1 Homepage
Today's date and three do's (tick inline). Today's calendar events. Top 5 emails by priority not yet handled. Tasks due today or overdue. Tracker quick-tick row (all daily_bool and weekly_count trackers). Hours this week vs targets per area. Weekly goals progress. Daily briefing text (Claude, generated 07:00, regenerate button). AI spend this month.

### 6.2 Agenda
Week view and day view of `calendar_events` plus scheduled tasks overlaid in a different colour. Create, edit, delete events (writes to iCloud). Sync-now button and last-synced timestamp. Multiple iCloud calendars selectable.

### 6.3 Mail
Unified inbox, sorted by priority. Filters: account, category, area, needs_reply, unhandled. Row shows account colour, from, subject, one-line summary, priority badge. Actions: mark handled, override priority/category, "create task from email" (pre-fills task with subject and link to the email). Opening a row shows the stored snippet and a "open in Gmail" link built from the message id. No sending.

### 6.4 Tasks
List and Eisenhower board (four quadrants, drag between them). Fields per section 5. Quick-add bar accepts plain text and, if it contains dates or areas in natural language, offers to parse it via Claude. "Suggest a slot" opens a panel: Pozzy computes free slots for the next 7 working days, Claude ranks the top 3 with a reason, accept writes the event to iCloud and sets status scheduled. Done tasks are logged to hours if `estimated_minutes` is set (optional prompt to confirm actual minutes).

### 6.5 Goals
Weekly goals for the current week with progress, plus the three do's for today and tomorrow. Setting tomorrow's do's in the evening is the intended flow. Rollover job at 00:05: any undone do from yesterday is copied to today with `rolled_from_date` set; a do rolled twice shows a warning badge. Optional "suggest three do's" (Claude picks from urgent/important tasks and deadlines).

### 6.6 Tracking
Trackers grouped by area. Weekly grid (Mon–Sun columns) for bool and count types; numeric and duration types get a line chart over the last 8 weeks. Streaks and weekly completion percentage. Create, edit, archive trackers.

### 6.7 Hours
Log minutes per area/tag, optionally linked to a task. Week table with per-area totals against targets. Simple timer (start/stop) that creates a log on stop.

### 6.8 Capture (quick inbox)
One text box, always reachable from the top bar. Submit stores raw text immediately, then Claude proposes what it is (task, event, weekly goal, note, tracker entry) with parsed fields. Wouter confirms or edits before anything is created. Unprocessed captures listed on the Capture page. This is also the endpoint the Telegram bot will hit in v2.

### 6.9 Study
Courses with period and ECTS. Deadlines per course; creating a deadline auto-creates a linked task with `important = true` and `urgent` flipping on automatically 3 days before due. Internship application tracker as a kanban (found, applied, interview, offer, rejected) with next-step dates that surface on the homepage.

### 6.10 Notes
Markdown notes with area and tags, pinned notes on top. Deliberately minimal; not a second brain.

### 6.11 Weekly review
Sunday 18:00 job computes the stats snapshot: goals hit/missed, three-do completion rate, tracker completion per tracker, hours per area vs target, tasks done, tasks rolled, emails handled. Claude writes a short reflection from the snapshot and drafts next week's goals from open tasks and deadlines. Wouter edits, adds his own notes, and finalises. Finalising creates next week's `weekly_goals`.

### 6.12 Settings
Working window, timezone, hour targets per area, calendar and mail accounts (add/remove, test connection), AI kill switches, briefing time, model selection.

## 7. Background jobs (APScheduler)

| Job | Schedule |
|---|---|
| calendar_sync | every 10 min |
| mail_sync_and_classify | every 15 min |
| three_do_rollover | daily 00:05 |
| deadline_urgency | daily 00:10 (flip urgent on tasks with due_date within 3 days) |
| daily_briefing | daily 07:00 |
| weekly_review_draft | Sunday 18:00 |
| ai_cost_rollup | daily 23:55 |

Jobs must be idempotent and must log to an `job_runs` table (name, started, finished, ok, message) shown in Settings so failures are visible.

## 8. API surface (summary)

REST, JSON, all under `/api`. One blueprint per module: `auth` (verify), `tasks`, `dos`, `goals`, `trackers`, `hours`, `calendar`, `mail`, `captures`, `notes`, `study`, `reviews`, `settings`, `ai`. Standard CRUD per resource plus action endpoints: `POST /tasks/{id}/suggest-slot`, `POST /tasks/{id}/schedule`, `POST /captures/{id}/process`, `POST /calendar/sync`, `POST /mail/sync`, `POST /ai/briefing`, `POST /reviews/{week}/finalize`.

## 9. Build order (single v1, but in this sequence so each step is testable)

1. Repo scaffold, Flask + SQLAlchemy + Alembic, Vue + router + auth guard, Supabase Auth wired end to end, deployed to Railway with a hello endpoint. Nothing else until this deploys.
2. Areas, Settings, Tasks (CRUD, Eisenhower board), Goals (weekly goals, three do's, rollover job).
3. Trackers, Hours, Notes, Study. Homepage v1 from local data.
4. Calendar: CalDAV read sync, Agenda views, then write.
5. Scheduling: free-slot engine, Claude ranking, accept → iCloud.
6. Mail: IMAP sync, Haiku classification, unified inbox, task-from-email.
7. Capture with Claude parsing. Daily briefing. AI cost tracking.
8. Weekly review job and page.
9. PWA manifest + service worker, mobile layout pass. Telegram bot (v2 start).

## 10. Things Wouter must provide before building

Supabase project (URL, anon key, service key, Postgres connection string). Anthropic API key. Apple app-specific password and Apple ID email. App passwords for the three Gmail accounts and the Workspace account (each needs 2-step verification enabled). Railway project with two services. Decide the domain (e.g. pozzy.up.railway.app is fine for v1).

Env vars: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`, `ICLOUD_USERNAME`, `ICLOUD_APP_PASSWORD`, `MAIL_ACCOUNTS_JSON` (or per-account vars), `SECRET_KEY`, `TZ=Europe/Amsterdam`.

## 11. Explicitly out of v1

Sending or replying to email. Gmail API and labels. Telegram bot (input and notifications). Shared use or multi-user. Trading 212 or finance widgets. Native iOS app. Offline-first PWA sync. Recurring tasks (use trackers for recurring habits; recurring tasks are v2).

## 12. Open risks

CalDAV write reliability on iCloud is decent but not perfect; keep the task's `calendar_uid` so a failed write can be retried. IMAP app passwords stop working if 2-step verification is turned off. APScheduler in-process means a Railway redeploy restarts jobs; all jobs are idempotent so this is acceptable. Scope is large for a solo build; the build order exists so a half-finished v1 is still a working app.
