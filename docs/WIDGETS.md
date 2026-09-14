# Homepage widgets

Each widget under `web/src/components/home/` fetches its own data on mount and renders nothing when its API call fails. Stream E assembles `HomeView.vue` in this order (plan 6.1 layout: do's and events top, then emails and tasks due, then trackers and hours, then goals and briefing, AI spend bottom).

| Order | Component | Data | Stream |
|---|---|---|---|
| 1 | `ThreeDosWidget.vue` | `GET /api/dos?date=today`, inline tick, add when fewer than 3 | A |
| 2 | `TodayEventsWidget.vue` | `GET /api/calendar/events?start=today&end=tomorrow`, today's events (all-day first) plus scheduled tasks not yet on iCloud. Local mirror only, no CalDAV call. | B |
| 3 | `TopEmailsWidget.vue` | `GET /api/mail/top` (Settings `mail_top_count`, default 5), unhandled emails by effective priority then date, account colour dot, priority badge, subject links to Gmail, inline mark handled. Renders nothing when the call fails; shows "Inbox handled." when empty. | C |
| 4 | `TasksDueWidget.vue` | `GET /api/tasks?due=today_or_overdue`, inline complete | A |
| 5 | `TrackerRowWidget.vue` | `GET /api/trackers/week`, one chip per daily_bool and weekly_count tracker, tap to tick today. Renders nothing when there are no such trackers. | A |
| 6 | `HoursWeekWidget.vue` | `GET /api/hours/week`, bar per area against Settings targets | A |
| 7 | `WeeklyGoalsWidget.vue` | `GET /api/goals`, tick and +1 inline | A |
| 8 | `DeadlinesWidget.vue` | `GET /api/study/upcoming?days=14`, deadlines and application next steps. Renders nothing when empty. | A |
| 9 | `BriefingWidget.vue` | `GET /api/ai/briefing` (today), paragraphs of text with source and time, Generate/Regenerate button calling `POST /api/ai/briefing`. Shows a hint when no briefing exists yet. | D |
| 10 | `AiSpendWidget.vue` | `GET /api/ai/spend`: month cost against Settings `ai_monthly_budget_usd`, today's cost, 7-day bars, cost per feature, collapsible recent calls with errors. | D |

Widgets are `<section class="card widget">` blocks; a two-column grid at 900px and up works with them as-is.
