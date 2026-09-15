# Pozzy progress

## Account names on mail, steadier loader, galaxy blue mark, event drag on the agenda, 2026-09-15 (deployed)

- Mail: email cards, the detail dialog, the account filter, the top emails widget and Settings show the account name derived from the address (wout.altepost, altepostwout, wjaltepost, wout@alpacaai) with the MAIL_ACCOUNTS_JSON label (Mail 1, Personal, Important, Work) as a tag. Presentation only (`web/src/lib/mail.js`), so env syncs, which reset labels, cannot undo it.
- Loader: the hidden content is absolutely positioned while loading so the gate keeps one height and the figure no longer drifts down as widgets arrive; the mark spins instead of breathing.
- Brand colour: galaxy blue #2A4B7C (dark #7C9CD9). favicon.svg recoloured at source; logo.png, pwa-192, pwa-512, pwa-512-maskable and apple-touch-icon recoloured by mapping the red hue to the blue one with shading kept (scratch PIL script). Tokens `--brand` and `--brand-soft` in both schemes. Olive green would be a one-line token change plus the same recolour.
- Agenda: drag an event to move it (keeps its duration, across days, 15 minute steps) or drag its bottom edge to resize; ghost preview while dragging; release sends `PUT /api/calendar/events/<id>` with the new start and end and a toast confirms. Recurring occurrences stay read-only. No API change.

Verification: Playwright on the local stack. With the API throttled the figure's position was sampled six times over 1.5 seconds and did not move; the mark carries the spin animation. Mail rows show the derived names and tags. The event drag was tested with the PUT intercepted in the browser so nothing reached iCloud: moving a block 88px down produced a ghost two hours later and a request body with start and end shifted by two hours and the same duration; the resize grip produced a body with the original start and a later end. Zero console errors.

## Capture dialog, tasks list, dialogs everywhere, loading gate, live habits chart, 2026-09-15 (deployed)

Five notes from Wouter.

- Capture is a button in the top bar (and Cmd or Ctrl plus K) that opens a dialog with the whole flow: write, proposal, adjust, confirm. The Capture page keeps the inbox. `components/CaptureBar.vue` rewritten, uses `ProposalEditor` inside `UiModal`.
- Tasks is one list grouped by due date (Overdue, Today, Tomorrow, Next seven days, Later, No date, Done) with an All / Urgent / Important switch and urgent and important chips on each row. Board, quadrant drag and drop and the side panel are gone (docs/V2.md records how to get the board back). Editor in a dialog.
- New `UiModal` (centred dialog from 700px, sheet below) replaces the side panels on Tasks, Agenda, Mail and Study. Softer motion: dialogs settle on a spring curve, route changes fade and rise, new tokens `--dur-modal`, `--dur-route`, `--ease-spring`. Motion spec updated in docs/briefs/DESIGN.md.
- `UiLoadGate` plus `useReady` / `useLoadGateHost` / `useLoadTask` in `composables/useReady.js`: the homepage waits for all ten widgets and reveals them together behind a breathing mark; Agenda, Tasks, Goals, Mail, Tracking, Hours, Capture, Study, Notes, Review and Settings gate on their first loads. Skeletons on those pages are replaced. An 8 second guard opens the gate regardless.
- Tracking: `GET /api/trackers/series?weeks=N|all` returns every tracker's daily points and weekly rows (with `met_days` for daily habits) on one range. `TrackerSeriesChart.vue` sits at the top of the page: percent of target per week, one colour per habit, legend toggles persisted in localStorage, range 4w / 12w / 26w / All, hover tooltip with real values. It refetches whenever the week grid reloads (ticks, entries). Test in `api/tests/a/test_trackers.py` (215 green).

Verification: Playwright on the local stack against Supabase. Home shows the figure with content hidden, then reveals nine rendered widgets together (the tenth has nothing to show). Capture dialog opens from the button and from Cmd plus K, focuses the textarea, closes on Escape. Task, event and mail dialogs open; tasks group into sections. Live chart renders in both themes, a legend chip hides its series, the tooltip follows the pointer. Phone: capture opens as a sheet, no overflow. Zero console errors, zero failed API calls. Screenshots: docs/design-screens/home-loading-*, capture-dialog-*, capture-sheet-*, tasks-*, tasks-dialog-*, agenda-dialog-*, mail-dialog-*, trackers-desktop-*.

## Tracker charts, agenda drag-to-create, spend rounding, 2026-09-15 (deployed)

- Tracking: clicking a habit name opens its chart for the whole run. `GET /api/trackers/<id>/history?all=1` starts at the week of the tracker's creation or its earliest entry, whichever is older, and returns `weeks` alongside `points` and `weekly`. Value trackers plot daily values, bool and count trackers plot weekly totals against the weekly target (7 for daily habits). LineChart now sizes its viewBox to the container instead of stretching. Test in `api/tests/a/test_trackers.py`.
- Agenda: press and drag on empty grid selects a range in 15 minute steps and opens a quick popover (`components/agenda/EventPopover.vue`) beside the column with title, day, start, end, calendar and Create; "More options" opens the full side panel with the same values. A plain click gives a one hour slot from the nearest half hour as before. Touch keeps the tap-to-sheet flow. Existing events still open in the side panel. Store, API and the calendar write path are unchanged.
- AI spend: every amount shows two decimals.

Verification: Playwright against the local API and Supabase data. Drag from 18:00 to 19:30 on a free column produced a ghost "18:00 to 19:30" and a popover with those times; a click at 14:10 gave 14:00 to 15:00; the popover flips left on the last column, clamps inside the grid at the bottom, closes on Escape, and "More options" carries the title into the side panel. A tap at 390px opens the sheet, not the popover. Tracker chart row opens on the habit name in light and dark. Spend widget reads "$0.58 this month of $10.00, $0.06 today". No console errors, no failed API calls, backend 214 green. Screenshots: docs/design-screens/agenda-drag-popover-*, agenda-more-panel-*, agenda-popover-bottom-*, trackers-chart-*.

## Briefing replies, glass cards, widget links, 2026-09-15 (deployed)

Three notes from Wouter after the design pass.

- Briefing reply (functional). Migration `g1000000notes` adds `daily_briefings.notes_json` (applied to Supabase). `POST /api/ai/briefing/notes` stores a note; with AI on, `claude_client.reply_briefing` (prompt `briefing_reply`, switch `ai_enabled.briefing`, smart model) returns an acknowledgement, the rewritten briefing and proposed actions. `briefing.validate_actions` keeps only allowlisted types (`mark_email_handled`, `complete_task`, `drop_task`, `add_do`, `add_note`, `set_hour_target`) whose ids and area names come from the candidates it was given, at most six. Nothing is applied until `POST /api/ai/briefing/notes/<i>/apply` runs the ticked ones through the owning services; each action is idempotent and reports ok or an error. With AI off the note is kept, the deterministic text quotes it, and no actions are proposed. Notes are passed to every later regeneration of the same day. Contract in docs/AI_CONTRACTS.md, tests in `api/tests/e/test_briefing_notes.py` (214 green in total).
- BriefingWidget: reply column on the right from 900px, a Reply button and sheet below that. Thread bubbles, proposed changes as pre-ticked checkboxes with the model's reason, Apply, textarea with Cmd/Ctrl plus Enter.
- Glass cards: translucent surface with backdrop blur over a fixed ambient layer, inner top highlight, reduced-transparency fallback; sheets share the material. Decisions and tokens in docs/briefs/DESIGN.md.
- Widget click-through: every homepage widget card except the briefing links to its route; controls inside the card keep working without navigating. Composable `web/src/composables/useWidgetLink.js`.

Verified locally against Supabase with a real Claude call: note "The Railway deploy issues have been fixed. The Ace and Tate email is not my concern." produced a rewritten briefing without the deploy paragraph and four "mark handled" proposals (the Ace & Tate email and three Railway build failures), nothing applied. Widget clicks land on /tasks and /agenda at 1440 and 390; no overflow at 390, no console errors, no failed API calls. Screenshots: docs/design-screens/home-*.png and home-briefing-reply-*.png.

## Design pass, 2026-09-15 (deployed)

Presentation only: no API, store, router, logic or data changes. Spec in docs/briefs/DESIGN.md, product record in PRODUCT.md, direction contract in the impeccable surface brief for web/src/App.vue. Backend suite 209 green, `npm run build` green, `impeccable detect` reports only the deliberate Geist choice.

What changed:
- Tokens in `web/src/style.css` (colour light and dark, type scale, spacing, radii, shadows, motion, layers), Geist self-hosted from `web/public/fonts`, Phosphor icons (`@phosphor-icons/vue`, the one new dependency).
- Shared components under `web/src/components/ui/`: UiButton, UiField, UiCard, UiBadge, UiEmpty, UiSkeleton, UiSegmented, UiSheet (bottom sheet with drag to dismiss), UiToast plus `useToast`, PageHeader, and `useMediaQuery`. Every view uses them; the 47 hard-coded colours and the six competing toolbar and header patterns are gone.
- App shell: 56px top bar with the mark, the capture field and the user; a 232px rail from 1024px; a nav sheet below that. Editors (task, event, mail detail, application) are a sticky side panel on desktop and a sheet on the phone.
- All twelve views and the login screen rewritten onto the vocabulary; ten homepage widgets share one card frame with a title row and a compact empty state.
- Motion: press feedback, hover on fine pointers only, popover from the capture field, side panel slide, sheet on the drawer curve, drag lift on the Eisenhower board and application kanban, toast. All transform and opacity, all under 300ms except the sheet, reduced motion honoured everywhere.
- PWA: icons rendered from Group.png on the bone field, favicon from favicon-svg.svg, manifest and theme colours from the tokens.

Decisions taken at the (skipped) image gate, option 3:
- Both colour schemes, following the system by default, plus a sun or moon toggle in the top bar and nav sheet (added on request after the deploy; stored per device).
- Comfortable density, closer to compact than the inspo.
- Plain CSS tokens and shared components; one dependency for icons, no UI library.
- Desktop first with a 390px pass on every view.
- Brand red reserved for the logo, the today marker, the current time line, the running timer lamp and the focus ring; interactive accent is ink. Reason: the seeded Work area is red.
- Geist as the single self-hosted family. The impeccable detector flags it as overused; kept because this is an Operate surface where a workhorse sans with tabular figures is the right tool and the character comes from the logo and layout.
- Asset discrepancy: `Branding/pozzy-svg.svg` is green (#2E7338) while the other three assets are red. The UI uses favicon-svg.svg and pozzy.png; the SVG wordmark is unused until confirmed.

Verification: 52 screenshots in docs/design-screens (12 routes plus login, 1440 and 390, light and dark) captured with Playwright against the local API and real Supabase data. No horizontal scroll at 390 on any route, zero console errors, zero failed API calls, keyboard focus visible on the first eight tab stops of the shell. Animation review against the review-animations standard: one finding (a keyframe on the tracker tick toggle) fixed; verdict approve.

Deferred to docs/V2.md: replacing window.prompt and window.confirm with inline confirms (logic change), the Work area colour, the wordmark SVG.

Deployment: approved by Wouter on 2026-09-15 after the screenshot review, pushed to main, Railway web and api deploys 10:14 CEST both SUCCESS. Production verified: Geist served and loaded, manifest and icons live, login renders with no page errors, api health db true and scheduler running.

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
- Production only: every scheduled job failed with psycopg `DuplicatePreparedStatement` / `InvalidSqlStatementName` because the Supabase transaction pooler (pgbouncer) does not support server-side prepared statements once connections are multiplexed. `config.py` now passes `prepare_threshold=None` to psycopg for Postgres URLs.
- Production only: the Railway `MAIL_ACCOUNTS_JSON` variable was 342 characters of invalid JSON (the M1 `set -a; source .env` export mangled the quoted JSON), so every mail sync reported "No password for this account". Re-set from `.env` through a subprocess call with no shell, verified by hash. DEPLOY.md now says to set that variable that way.

Known gaps: see docs/V2.md. Short version: recurring iCloud occurrences are read-only, the hours timer is browser-local, no thread grouping in Mail, Haiku prompt caching not yet effective, prices hardcoded, no automated browser tests.

Open issues:
- Local login for automated checks was done with an HS256 token minted from `SUPABASE_JWT_SECRET` (the API accepts it as the documented fallback); there is no Supabase user password in `.env`, so a Playwright login flow is not possible without one.
- Calendar selection in Settings currently includes Reminders and Holidays; untick them once so all-day noise stays out of the Agenda.

Production evidence, `job_runs` on Supabase after the api restart with `RUN_SCHEDULER=1` at 21:43 CEST (scheduler confirmed running via `/api/health`):
- calendar_sync 21:50 ok: 10/10 calendars, 2 inserted, 5 updated, 61 unchanged, 6 deleted.
- calendar_sync 22:00 ok: 10/10 calendars, 68 unchanged.
- mail_sync_and_classify 22:00 ok: 4 accounts, nothing new (backfill done earlier the same day: 355 emails, 354 classified by Claude).
- Before the pooler fix every run since 17:15 had failed with the prepared-statement errors listed above; the first mail run after re-setting `MAIL_ACCOUNTS_JSON` (21:45) synced 14 new emails.
- A stale `mail_accounts` row for the truncated address `wout@alpacaai` (from the M1 open issue) was disabled through `PATCH /api/mail/accounts/<id>`; the upsert now disables any row whose address leaves `MAIL_ACCOUNTS_JSON`.

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
