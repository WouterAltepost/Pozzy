# Vue routes and nav

Stream E wires these into `web/src/router/index.js` and the nav in `App.vue`. Every view below is a guarded route (not `meta.public`). Route names are referenced by widgets and views via `RouterLink :to="{ name }"`, so keep the names exactly as listed.

| Nav order | Path | Route name | View file | Nav label | Stream |
|---|---|---|---|---|---|
| 1 | `/` | `home` | `views/HomeView.vue` | Home | M1 / E |
| 3 | `/tasks` | `tasks` | `views/TasksView.vue` | Tasks | A |
| 4 | `/goals` | `goals` | `views/GoalsView.vue` | Goals | A |
| 6 | `/trackers` | `trackers` | `views/TrackersView.vue` | Tracking | A |
| 7 | `/hours` | `hours` | `views/HoursView.vue` | Hours | A |
| 9 | `/study` | `study` | `views/StudyView.vue` | Study | A |
| 10 | `/notes` | `notes` | `views/NotesView.vue` | Notes | A |
| 99 | `/settings` | `settings` | `views/SettingsView.vue` | Settings | A |

Gaps in the order are reserved: 2 Agenda (B), 5 Mail (C), 8 Capture (D), 11 Weekly review (D).

## Stream A notes for E

- `web/src/stores/areas.js` is a shared read-only cache of the four areas (`useAreasStore`), used by A's views and widgets. Other streams may use it; do not duplicate it.
- `web/src/lib/dates.js` holds shared date helpers (today, mondayOf, formatDay, minutesToHours).
- `SettingsView.vue` has two empty mount points, `#settings-calendar-accounts` and `#settings-mail-accounts`, inside the Integrations card. E replaces those divs with `<CalendarAccounts />` (B) and `<MailAccounts />` (C) and imports the components at the path each stream documents here.
- Shared small components under `web/src/components/shared/`: `AreaSelect`, `AreaDot`, `TagsInput`, `WeekNav`.
