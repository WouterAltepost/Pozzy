# Vue routes and nav

Stream E wires these into `web/src/router/index.js` and the nav in `App.vue`. Every view below is a guarded route (not `meta.public`). Route names are referenced by widgets and views via `RouterLink :to="{ name }"`, so keep the names exactly as listed.

| Nav order | Path | Route name | View file | Nav label | Stream |
|---|---|---|---|---|---|
| 1 | `/` | `home` | `views/HomeView.vue` | Home | M1 / E |
| 2 | `/agenda` | `agenda` | `views/AgendaView.vue` | Agenda | B |
| 3 | `/tasks` | `tasks` | `views/TasksView.vue` | Tasks | A |
| 4 | `/goals` | `goals` | `views/GoalsView.vue` | Goals | A |
| 6 | `/trackers` | `trackers` | `views/TrackersView.vue` | Tracking | A |
| 7 | `/hours` | `hours` | `views/HoursView.vue` | Hours | A |
| 9 | `/study` | `study` | `views/StudyView.vue` | Study | A |
| 10 | `/notes` | `notes` | `views/NotesView.vue` | Notes | A |
| 99 | `/settings` | `settings` | `views/SettingsView.vue` | Settings | A |

Gaps in the order are reserved: 5 Mail (C), 8 Capture (D), 11 Weekly review (D).

## Stream A notes for E

- `web/src/stores/areas.js` is a shared read-only cache of the four areas (`useAreasStore`), used by A's views and widgets. Other streams may use it; do not duplicate it.
- `web/src/lib/dates.js` holds shared date helpers (today, mondayOf, formatDay, minutesToHours).
- `SettingsView.vue` has two empty mount points, `#settings-calendar-accounts` and `#settings-mail-accounts`, inside the Integrations card. E replaces those divs with `<CalendarAccounts />` (B) and `<MailAccounts />` (C) and imports the components at the path each stream documents here.
- Shared small components under `web/src/components/shared/`: `AreaSelect`, `AreaDot`, `TagsInput`, `WeekNav`.

## Stream B notes for E

- Settings mount point `#settings-calendar-accounts`: replace with `<CalendarAccounts />` imported from `web/src/components/settings/CalendarAccounts.vue`. It is self-contained (own store, own API calls) and needs no props.
- `web/src/stores/calendar.js` (`useCalendarStore`) is shared by the Agenda view, the settings component and the sync bar. `TodayEventsWidget` and `AgendaGrid` link to route names `agenda` and `tasks`.
- The agenda does not depend on the sync running: it renders the local `calendar_events` mirror and shows "Not synced yet" until the job or the Sync now button has run.
