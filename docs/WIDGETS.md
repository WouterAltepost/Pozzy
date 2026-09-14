# Homepage widgets

Each widget under `web/src/components/home/` fetches its own data on mount and renders nothing when its API call fails. Stream E assembles `HomeView.vue` in this order (plan 6.1 layout: do's and events top, then emails and tasks due, then trackers and hours, then goals and briefing, AI spend bottom).

| Order | Component | Data | Stream |
|---|---|---|---|
| 1 | `ThreeDosWidget.vue` | `GET /api/dos?date=today`, inline tick, add when fewer than 3 | A |
| 2 | `TodayEventsWidget.vue` | calendar events today | B |
| 3 | `TopEmailsWidget.vue` | top 5 unhandled emails by priority | C |
| 4 | `TasksDueWidget.vue` | `GET /api/tasks?due=today_or_overdue`, inline complete | A |
| 5 | `TrackerRowWidget.vue` | `GET /api/trackers/week`, one chip per daily_bool and weekly_count tracker, tap to tick today. Renders nothing when there are no such trackers. | A |
| 6 | `HoursWeekWidget.vue` | `GET /api/hours/week`, bar per area against Settings targets | A |
| 7 | `WeeklyGoalsWidget.vue` | `GET /api/goals`, tick and +1 inline | A |
| 8 | `DeadlinesWidget.vue` | `GET /api/study/upcoming?days=14`, deadlines and application next steps. Renders nothing when empty. | A |
| 9 | `BriefingWidget.vue` | daily briefing text, regenerate button | D |
| 10 | `AiSpendWidget.vue` | AI spend this month | D |

Widgets are `<section class="card widget">` blocks; a two-column grid at 900px and up works with them as-is.
