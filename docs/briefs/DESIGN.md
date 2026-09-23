# Pozzy design system (v1 design pass, 2026-09-15)

Implementation spec for the presentation-only design pass. Source of truth for every token, component and per-view layout in `web/`. The direction contract lives in the impeccable surface brief for `web/src/App.vue`; PRODUCT.md holds product truth. This file describes what is built; the section "Decisions" records the choices the kickoff brief asked for.

## 1. Direction in one paragraph

Pozzy is a desk instrument, not a SaaS dashboard. A matte stone housing carries raised bone panels separated by hairlines; numbers are tabular; one red lamp marks "now". Brand red is the logo, the today marker, the current time line, the running timer and the focus ring, nothing else. Primary actions are ink, secondary are outlined, area and mail account colours come from the database and are data, never decoration. Both colour schemes follow the system.

## 2. Decisions (asked for at the image gate, taken under option 3)

| Question | Decision | Reason |
|---|---|---|
| Light, dark or both | Both, following `prefers-color-scheme` by default, with a sun or moon toggle in the top bar and the nav sheet (added on request, 2026-09-15). The choice is stored per device in localStorage as `pozzy.theme` and forces `data-theme` on the root | Morning use is daylight at a desk, evening planning is often on the phone in the dark |
| Density | Comfortable, closer to compact than the inspo | Daily tool with twelve routes and ten widgets; the inspo's airiness is for marketing screenshots, not a week planner |
| Implementation | Plain CSS custom properties plus shared Vue components; one dependency added, `@phosphor-icons/vue` for icons | No UI library: the existing markup is small enough to normalise by hand, and a library would fight the token system. Icons must come from a real set, so one tree-shakeable icon package |
| Desktop first or mobile first | Desktop first with a 390px pass on every view | Primary use is the laptop; the phone is a check-in device |
| Logo colour as accent | Reserved: logo, now marker, focus ring only. Interactive accent is ink. Brand colour changed from red #AF1616 to galaxy blue #2A4B7C on 2026-09-15 (Wouter's request; olive green was the alternative). The SVG mark is recoloured at source, the PNG logo and PWA icons by hue mapping of the red pixels | Blue reads calmer next to the red Work area and the danger tone, and no longer collides with them |
| Card material | iOS-style glass (requested 2026-09-15): cards are `--surface` at 74% over a fixed ambient layer of two soft brand and info fields, `backdrop-filter: blur(18px) saturate(150%)`, a 1px white inner highlight on the top edge (7% in dark), hairline at 80%. Sheets use the same at 82% and 24px. `prefers-reduced-transparency` restores the solid surface and hides the ambient layer | The blur needs something behind it, so the ambient layer exists only to be blurred. Kept subtle so text contrast on the cards is unchanged |
| Widget click-through | Every homepage widget card except the briefing is a link to its route (`role="link"`, tabindex, Enter). Clicks on controls inside the card (checkbox, button, link, input) do not navigate; a text selection does not navigate. Hover lifts the card to `--shadow-2`, press scales to 0.995 | Requested 2026-09-15. The briefing card instead hosts the reply column |
| Popups over panels | Every editor and detail view opens in `UiModal`: a centred glass dialog from 700px, the bottom sheet below that. The sticky side panels on Tasks, Agenda, Mail and Study are gone. The agenda quick popover stays for slot creation (requested 2026-09-15) | One way to open things everywhere, and the page underneath never reflows |
| Capture | One "Capture" button in the top bar (Cmd or Ctrl plus K) opens the capture dialog: textarea, then the proposal editor in the same dialog, Confirm creates. The search-bar look is gone (requested 2026-09-15) | It is a function, not a search |
| Tasks layout | One list grouped by due date (Overdue, Today, Tomorrow, Next seven days, Later, No date, Done) with urgent and important as chips and an All / Urgent / Important switch. The Eisenhower board and its drag and drop are removed (requested 2026-09-15; the old view is in git history at commit 5a6e266) | He does not think in quadrants; due date is the axis he plans on |
| Loading | `UiLoadGate` holds a page behind one figure (the mark spinning plus a label); the hidden content is taken out of the flow so the figure never moves while widgets arrive until its first loads settle, then reveals everything at once with a rise and fade. Homepage widgets report into the gate; every other view passes `ready` from `useReady`. The figure appears only after 140ms so fast loads never flash it (requested 2026-09-15) | Widgets arriving one by one read as broken; one reveal reads as done |
| Tracking chart | A live multi-series chart at the top of Tracking: percent of target per week for every habit, one colour per habit from an eight-colour palette, legend chips toggle series (persisted per device), range 4w / 12w / 26w / All, hover tooltip with the real values. Habits without a target are scaled to their best week and marked "scaled" in the legend (requested 2026-09-15) | One comparable axis across habits with different units |
| Fonts | Self-hosted Geist (variable, 300 to 800), latin subset, `font-display: swap`; no runtime font requests | One workhorse sans for an Operate surface; tabular figures and a real medium weight; the wordmark serif lives only inside the logo image |
| Logo assets | New mark delivered 2026-09-16: `Branding/pozzy-new.svg` (1681 by 1611, navy #082247 with gold #C49A4E, teal and white, transparent) is copied verbatim to `web/public/favicon.svg` and used for the browser icon, the top bar mark (26px), the loading figure (34px) and the login page (88px, with a text wordmark beneath, since the mark carries no wordmark). PWA icons and the Apple touch icon are the PNG (`pozzy-new2.png`) composited on the bone field at 78% of the tile, the maskable one at 56% so it stays inside the safe zone. `logo.png` is the mark alone at 512px. `web/public/mark-dark.svg` is the same SVG with its navy fills swapped for the dark brand blue #8AA6D9 (gold, teal and white untouched), used wherever the mark sits on a dark surface (top bar, loading figure, login) via the theme composable. The previous assets live in `Branding/Archive` | One source file for every vector use, rasters only where the platform needs them |

## 3. Tokens (CSS custom properties in `web/src/style.css`)

### Colour, light (default)

```
--bg: #F2F1ED            page housing
--surface: #FBFAF8       raised panel, card, input
--surface-2: #E9E8E3     inset areas, toolbars, table heads, disabled fills
--surface-3: #DFDED8     pressed, selected rows, drop targets
--ink: #191A1C           primary text, primary button fill
--ink-2: #4A4C52         secondary text
--ink-3: #7B7E86         muted text, placeholders (4.6:1 on --surface)
--line: #DAD9D3          hairline
--line-2: #C3C2BB        stronger rule, input border
--brand: #082247         logo navy, now marker, focus ring (red #AF1616 until 2026-09-15, galaxy blue #2A4B7C for a day, the new mark's navy since 2026-09-16)
--brand-soft: #F6E1E1    now marker fill, today column
--on-ink: #F7F6F2        text on --ink
--ok: #1F7A4D  --ok-soft: #E2F1E8
--warn: #A35E08  --warn-soft: #F8EBD6
--danger: #B3261E  --danger-soft: #F8E1DF
--info: #2F5FB3  --info-soft: #E1E9F6
```

### Colour, dark (`@media (prefers-color-scheme: dark)`)

```
--bg: #141518  --surface: #1C1E22  --surface-2: #24262B  --surface-3: #2D3036
--ink: #ECEBE6  --ink-2: #B6B5B0  --ink-3: #8A8B91
--line: #2C2E34  --line-2: #3D4048
--brand: #8AA6D9  --brand-soft: #1B2740  --on-ink: #16171A
--ok: #5CC48F  --ok-soft: #1B3328  --warn: #E1A64E  --warn-soft: #3A2C16
--danger: #E86B62  --danger-soft: #3D2220  --info: #7FA3E6  --info-soft: #1F2A40
```

Priority badges: P1 `--danger`, P2 `--warn`, P3 `--info`, P4 `--ink-3`, each on its soft tint. Eisenhower quadrants: do `--danger`, schedule `--info`, delegate `--warn`, eliminate `--ink-3`, used as a 2px top rule and the quadrant label only. Area badges and dots: colour from the `areas` table via inline style, tint via `color-mix(in srgb, var(--area) 14%, transparent)`.

### Type

Family `Geist, system-ui, sans-serif`. Base 14px, line height 1.5. Fixed rem scale, ratio about 1.2:

```
--fs-xs: 0.6875rem (11)   labels, table heads, badges; letter-spacing 0.02em
--fs-sm: 0.75rem (12)     meta, hints
--fs-md: 0.8125rem (13)   dense body, rows
--fs-base: 0.875rem (14)  body
--fs-lg: 1rem (16)        h3, card titles
--fs-xl: 1.125rem (18)    h2, panel titles
--fs-2xl: 1.375rem (22)   h1 page titles; letter-spacing -0.01em
--fs-3xl: 1.75rem (28)    display: home date; letter-spacing -0.02em; line-height 1.15
```

Weights: 400 body, 500 labels and buttons, 600 titles. Every number that can be compared (times, minutes, counts, money) sets `font-variant-numeric: tabular-nums` via `.num`.

### Spacing, radius, elevation

```
--sp-1: 4px  --sp-2: 8px  --sp-3: 12px  --sp-4: 16px  --sp-5: 20px  --sp-6: 24px  --sp-8: 32px  --sp-10: 40px
--r-sm: 6px   badges, tags, table cells
--r-md: 8px   buttons, inputs, chips that are not pills
--r-lg: 12px  cards, panels, popovers
--r-xl: 16px  sheets
--r-pill: 999px  filter chips, tracker chips, nav items
--shadow-1: 0 1px 2px rgb(25 26 28 / 0.06), 0 1px 1px rgb(25 26 28 / 0.04)      raised panel
--shadow-2: 0 6px 16px -4px rgb(25 26 28 / 0.14), 0 2px 4px rgb(25 26 28 / 0.06) lifted card, popover
--shadow-3: 0 18px 44px -10px rgb(25 26 28 / 0.28)                                sheet, capture panel
```

Dark mode shadows keep the same shape with alpha 0.5, 0.6, 0.7.

### Motion

```
--dur-press: 120ms   --dur-hover: 160ms   --dur-ui: 200ms   --dur-panel: 240ms   --dur-sheet: 420ms
--ease-out: cubic-bezier(0.23, 1, 0.32, 1)
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)
```

Only `transform`, `opacity`, `background-color`, `border-color`, `color` and `box-shadow` animate. Hover motion is gated by `@media (hover: hover) and (pointer: fine)`. Under `prefers-reduced-motion: reduce` every transform transition collapses to an opacity or colour change of 120ms; the sheet fades instead of sliding.

Anything a finger can hold runs on a spring, not a curve (`web/src/lib/spring.js`, Apple's two parameters: damping ratio and response in seconds). Springs start from the current on-screen value and velocity, so they can be grabbed and reversed mid-flight. Defaults: damping 1.0 (no overshoot), response 0.3 to 0.4 s. Drags come from `composables/useDrag.js`: pointer capture, an 8px threshold that locks to one axis, a 100 ms velocity history handed to the spring on release; the landing point is projected from the flick (`project`, deceleration 0.998) and edges resist (`rubberband`).

### Layers

`--z-raised: 1`, `--z-sticky: 10` (side panels, table heads), `--z-bar: 20` (top bar, rail), `--z-sheet: 30` (mobile nav, capture panel), `--z-toast: 40`.

## 4. Typography rules and font loading

`@font-face` for Geist in `style.css` pointing at `/fonts/geist-latin.woff2` (variable, weight range 300 800, `font-display: swap`, latin unicode range). One family for everything. Headings never use the display serif; the wordmark exists only inside the logo image. Body measure caps at 68ch in Notes preview and Briefing. Display date on Home is the only 28px text in the app.

## 5. Components (`web/src/components/ui/`)

Every interactive component has default, hover, focus-visible, active, disabled and, where it applies, loading, error and empty. Focus is a 2px `--brand` ring with 2px offset, everywhere, including custom controls.

- **UiButton** `variant` primary (ink fill, on-ink text), secondary (surface, line-2 border), ghost (no border, surface-2 on hover), danger (danger-soft fill, danger text; primary danger only inside a confirm), link (inline, ink-2, underline offset 3px). `size` sm (28px) md (34px). `loading` swaps the label for a 14px ring spinner and keeps width. Press: `scale(0.97)` over `--dur-press`. Icon slot left or right at 16px.
- **UiInput, UiSelect, UiTextarea, UiField** label above (`--fs-xs`, `--ink-2`, 500), control 34px, `--surface` fill, `--line-2` border, `--r-md`; hover `--ink-3` border; focus ring; `invalid` sets `--danger` border and an error line below in `--danger`; hint line in `--ink-3`. Select uses a Phosphor caret drawn as background. Never placeholder as label.
- **UiCheck** checkbox and switch share the ink fill when on; 18px box, `--r-sm`.
- **UiCard** `--surface`, `--line` hairline, `--r-lg`, `--shadow-1`, padding `--sp-4` (`--sp-5` on desktop). Title row: `--fs-lg` 600 with an optional `meta` slot right-aligned in `--fs-sm --ink-3`. `flush` removes padding for lists and tables. Nested cards are not allowed; inner grouping uses `--surface-2` insets.
- **Widget frame** = UiCard with a title row and an optional right link; widgets keep their own data logic.
- **UiBadge** tone neutral, brand, ok, warn, danger, info; `--fs-xs` 500, 20px tall, `--r-sm`, tinted fill and coloured text. **PriorityBadge** wraps UiBadge with P1..P4 tones. **AreaBadge** and **AreaDot**: colour from data.
- **UiEmpty** icon (Phosphor, 28px, `--ink-3`), title `--fs-base` 500, hint `--fs-sm`, optional action button. Replaces every "muted li" empty state.
- **UiSkeleton** lines and blocks with a 1.6s shimmer, reduced motion shows static `--surface-2`. Replaces "Loading...".
- **UiToast** bottom centre, `--surface` on `--shadow-3`, 4s, slides up 8px on `--ease-out`, one at a time; `useToast()` composable. Used for save confirmations that today are inline strings.
- **PageHeader** h1 left, toolbar slot right, wraps at 720px; toolbars use the `.toolbar` class only (retires `.head`, `.row head`, `.controls`).
- **UiTable** `th` `--fs-xs` uppercase-free 500 `--ink-3` with a `--line` bottom rule; rows separated by `--line` at 1px, hover `--surface-2`; numeric cells right-aligned with `.num`.
- **Side panel** (Agenda editor, Tasks editor, Mail detail): desktop `position: sticky; top: 72px`, width 360px, UiCard; under 900px it becomes a **UiSheet** from the bottom (see below).
- **UiSheet** full-width bottom sheet, `--r-xl` top corners, `--shadow-3`, grab handle, scrim `rgb(25 26 28 / 0.4)`. Opens on `--ease-drawer` 420ms, closes the same path; drag-to-dismiss with pointer capture, rubber-banding at the top, flick velocity threshold 0.11 px/ms; Escape and scrim close; focus is trapped while open; reduced motion fades.
- **Nav rail** (desktop 1024 and up) 232px, items 36px tall `--r-pill`, icon 18px plus label, active item `--surface-3` fill with ink text, hover `--surface-2`. **Top bar** 56px, `--surface` with a `--line` bottom rule, sticky. **Mobile nav** is a UiSheet listing the same items in two columns.
- **CaptureBar** input sits in the top bar at 480px max, `--surface-2` fill, `--r-pill`; the proposal panel is a popover under it (`--shadow-2`, `--r-lg`, transform-origin top).
- **Drag and drop affordances** (Eisenhower, application kanban): grab cursor, on pointer down the card lifts (`--shadow-2`, `rotate(1.5deg) scale(1.02)`, 160ms ease-out), the drop target shows `--surface-3` fill and an ink hairline; on drop the card settles with 180ms ease-out. Keyboard alternative stays the existing move button in the editor.
- **UiModal** dialog: centred from 700px, `UiSheet` below; sizes sm 440, md 600, lg 780; glass material, scrim, Escape and scrim close, focus to the first field in the body and back on close, body scroll lock.
- **UiLoadGate** page loading figure: `ready` prop, 140ms grace before the figure, content stays mounted but hidden, inert and absolutely positioned (the gate keeps a fixed 56vh while loading), reveal 280ms fade plus 320ms rise on the spring curve; the mark spins 1.6s per turn.
- **TrackerSeriesChart** live habits chart: responsive SVG, palette of eight, legend chips, tooltip with guide line, range control.
- **LineChart** (trackers) stroke `--ink`, target line `--brand` dashed, points `--ink`, gridlines `--line`, axis text `--ink-3`; unchanged geometry.

## 6. Per-view layout (desktop 1440 / mobile 390)

Content max width 1180px inside the rail layout; page padding `--sp-6` desktop, `--sp-4` mobile. Every view starts with PageHeader.

- **Home**: display date; widget grid two columns from 900px (`minmax(0,1fr)` twice), one column below; order per docs/WIDGETS.md; each widget a card and a link to its route; the briefing card spans both columns and, from 900px, is itself a two-column grid: the text at 1.4fr and a reply column at 1fr behind a hairline (thread of your notes and Pozzy's replies as small bubbles, a dashed "Proposed changes" inset with checkboxes and an Apply button, a textarea with a send button, Cmd or Ctrl plus Enter sends). Below 900px the reply column becomes a "Reply (n)" button in the card head that opens the same content in a sheet.
- **Agenda**: PageHeader with week nav, view toggle (segmented control), date input, Sync now and New event; grid card flush; today column `--brand-soft` header text `--brand`; now line `--brand` 2px; events use account or area colour as a 3px left rule inside the block (allowed: it is data, under 1px rule exception because it is inside a block, not a card); editor in the side panel / sheet. Press and drag on empty grid (mouse or pen) selects a range in 15 minute steps with a dashed ghost block labelled with the times; release, or a plain click, opens a quick popover beside the column (title, day, start, end, calendar, Create, "More options" hands the values to the side panel). The popover flips to the left of the column when it would leave the grid and never sits below the grid bottom. On the phone a tap opens the sheet as before. Existing events move by drag and resize by their bottom edge (mouse or pen); recurring occurrences stay read-only. "Plan" in the header asks Pozzy for placements (open tasks, deadline prep, goal work): they appear as dashed ghost blocks in the grid (task in `--ok`, event in `--info`, 10% tint on the surface) with a small accept and deny button each, plus a dashed tray card above the grid listing every suggestion with its reason and Accept all / Deny all. Accepting a task schedules it (linked calendar event), accepting an event creates it; denying only removes the ghost. "New event" in the header and editing an existing event open the dialog (added on request, 2026-09-15).
- **Tasks**: PageHeader with quick add, All / Urgent / Important switch, area select, search, show done; sections by due date with small uppercase headings (Overdue in `--danger`); task rows are `--surface` cards with a checkbox, title, area, due badge, minutes, urgent and important chips; editor in the dialog with the slot suggestions below the form.
- **Goals**: two-column top row (today and tomorrow do's) then suggestions and weekly goals; do rows 40px with checkbox, editable title, rollover badge (warn tone when rolled twice); goal rows with a 6px progress bar in `--ink` on `--surface-3`.
- **Mail**: PageHeader with counts, Sync now, accounts link; filters as a chip row; list rows 56px with account colour bar 3px, priority badge, the account name derived from the address (wout.altepost, altepostwout, wjaltepost, wout@alpacaai) in the account colour, the MAIL_ACCOUNTS_JSON label (Mail 1, Personal, Important, Work) as a tag, from, subject, summary; detail in a large dialog. `lib/mail.js::accountName`.
- **Tracking**: week nav; the live all-habits chart card first, then one card per area, table with day columns; tick cells 32px `--r-md`, met `--ok-soft` with `--ok` mark, today column tinted `--brand-soft`; the habit name is a button with a caret that opens the chart row for the whole run since the tracker was created (value trackers plot daily values, bool and count trackers plot weekly totals with the weekly target as the dashed line); the chart viewBox follows its container width so nothing stretches.
- **Hours**: timer card first (display time in `--fs-3xl` tabular, area select, note, Start or Stop); totals table with 6px bars; log form; per-day lists.
- **Capture**: entry card with textarea and one primary button; inbox list of proposal cards; handled list collapsed.
- **Study**: deadlines list, courses table, kanban of five columns at 900px and up, two columns below, editor as a sheet on mobile.
- **Notes**: list rail 280px plus editor card; preview typeset at 68ch.
- **Review**: week nav; stat tiles as a four-up grid of insets (two-up mobile); reflection text; notes textarea; focus rows.
- **Settings**: cards in a single 720px column; job runs table with ok/failed badges; integrations components inherit the tokens. A "Rules for Pozzy" card (added 2026-09-16) holds two textareas: rules one per line and standing context; it sits above the AI kill switches.
- **Login**: centred 360px card on the housing with `pozzy.png` at 180px wide above the form.

Mobile (390px, from the Claude Design handoff `pozzy-mobile-app-design/project/Pozzy Mobile.dc.html` and `Pozzy Phone.dc.html`, implemented 2026-09-16): the shell is the drawer variant of the design (Turn 2 used it for every screen). Top bar: menu icon at the left, a full-width capture pill ("Capture anything", opens the capture dialog), the theme toggle at the right; the mark and log out live in the drawer. The drawer is 272px from the left with all twelve routes at 42px, the theme row, log out and the email at the bottom; it slides in 8px with a fade on ease-out over 240ms. The top bar and the drawer respect the iOS safe areas. Dialogs stay centred popups on the phone (the design's editor is a popup, not a sheet); only the briefing reply keeps the sheet.
- Home (phone): the six design cards in the design's order (three do's, Today, Briefing, Due today or overdue, Trackers today, Hours this week) followed by Top emails, Weekly goals, Deadlines and AI spend so every feature stays reachable.
- Agenda (phone, `components/agenda/AgendaMobile.vue`): title with "Week of" meta and the Week / Day segmented control; a status row with week arrows, the synced badge (tap to sync), iCloud, the count, Plan and New event icons. Week: a compact grid, 30px gutter and 30px per hour from 07:00 to 23:00, day headers show weekday and number, today in `--brand-soft`, events as 3px-barred blocks (info, recurring surface-2, linked ok, task dashed), suggestions dashed; tap a day to open it. Day: a seven-button strip (52px, active ink, today brand-soft) and a list card with start and end times, a 3px colour bar, title, location and badges, the now line between rows, suggestions as dashed rows with accept and deny; swipe the list 40px to change day. Drag to create and drag to move are desktop only.
- Tasks (phone): quick add and search hidden (capture does that); All / Urgent / Important switch, area select and Show done; each due group is a card with a 13px heading in the group colour and "N tasks"; rows are hairline rows with an 18px checkbox, title, due label at the right in colour, area, minutes and badges.
- Tracking (phone): title with "N of M met today" and New tracker; the live chart card; a Today card with tracker chips (tap to tick or enter a value); a This week card with one row per habit and seven 22px day cells (met ok-soft, partial warn-soft, empty surface-2, future transparent, today outlined), tap the name for its chart, edit link per row; a compact week nav in the card head.
- Hours (phone): title with "Xh this week" and a Log time button that opens a dialog with the log form; the timer card stacked; a By life area card with dot, bar and totals; an Entries card with a seven-day strip and that day's logs.
- The seven routes the handoff did not design got the same vocabulary (2026-09-16, second pass): a 22px title with a 12px meta line and one small primary action at the right; forms behind Add buttons that open dialogs; lists as cards with hairline rows.
  - Mail: title with the counts and Sync now; search plus a Filters toggle (badge with the active count) that reveals the filter selects; rows drop the category tag, area dot and summary, and the list shows 40 at a time with Show more.
  - Notes: title with the count and New note; search, area and tag in one row; the list is a card of hairline rows; the editor opens as a large dialog.
  - Study: title with open deadlines and applications; the three inline forms become Add buttons and dialogs; applications are stacked stage lists (empty stages hidden, no drag).
  - Goals and Review: compact week nav; Settings: two-up fields and the job runs table shows eight rows with Show all; Capture unchanged apart from spacing.
- The loading gate, glass cards, route and dialog motion, the planner and the briefing reply all apply on the phone.

## 7. Dark mode, focus, contrast, reduced motion

Tokens swap under `prefers-color-scheme: dark` unless `data-theme="light"` is set, and under `data-theme="dark"` regardless of the system; `composables/useTheme.js` owns the attribute and the theme-color meta. Text on surfaces meets 4.5:1 in both schemes (`--ink-3` on `--surface` is 4.6:1 light, 4.7:1 dark); badges keep 4.5:1 text on their soft tints. Focus is never removed; `:focus-visible` shows the brand ring. Reduced motion: no transforms, opacity and colour only, skeleton shimmer static, sheet fades.

## 8. PWA

Icons: `pwa-192.png`, `pwa-512.png`, `apple-touch-icon.png` rendered from `Group.png` unchanged on a `#FBFAF8` field with 12 percent padding (maskable variant with 20 percent). Favicon: `favicon-svg.svg` copied as `favicon.svg`. Manifest `theme_color #FBFAF8`, `background_color #F2F1ED`; `<meta name="theme-color">` carries both schemes.

## 9. Motion spec

| Moment | Spec |
|---|---|
| Button press | transform scale(0.97), 120ms ease-out; release 160ms |
| Hover on buttons, rows, nav items | background-color 160ms ease, gated to fine pointers |
| Checkbox, switch | background-color and border 160ms; check mark opacity 120ms |
| Popover (capture proposal, slot list, agenda quick event) | opacity plus scale(0.97) to 1, 200ms ease-out, transform-origin at the trigger |
| Agenda drag selection | ghost block follows the pointer 1:1, no transition; popover appears on release |
| Side panel appear (desktop) | opacity and translateX(8px) to 0, 240ms ease-out; disappear 160ms |
| Phone drawer (NavDrawer) | spring from the left edge, damping 1.0, response 0.36 s; the scrim's opacity is the drawer's progress; drag follows the finger 1:1, rubber-bands past open, a leftward flick (over 250 px/s) or a projected rest past half width closes it at the finger's speed; it leaves the way it came |
| Phone sheet (UiModal under 720px) | a bottom sheet with a grabber: spring up from the bottom edge, damping 1.0, response 0.4 s; grabber and head drag 1:1, rubber-band above rest, downward flick or projected rest past half height dismisses with the finger's velocity; the body scrolls natively |
| Agenda day swipe (phone) | the day list tracks the finger 1:1 and fades with distance; on release the flick is projected, past a third of the width (or over 250 px/s) the list leaves at that speed, the day changes and the next list arrives from the other side carrying the velocity; otherwise it springs home |
| Segmented control | one thumb springs between segments (damping 1.0, response 0.3 s); segments press to scale(0.96) |
| Drag and drop lift | shadow-2, rotate(1.5deg) scale(1.02), 160ms ease-out; drop target fill 160ms; settle 180ms |
| Toast | translateY(8px) plus opacity, 200ms ease-out in, 160ms out |
| Skeleton | 1.6s linear shimmer, static under reduced motion |
| Route change | out-in: old view fades 90ms, new view fades and rises 8px over 220ms on the spring curve (relaxed on request 2026-09-15; still no per-element choreography) |
| Dialog (UiModal, desktop) | scrim fades 200ms; panel materialises in place, opacity 200ms plus scale(0.96) to 1 over 340ms on the spring curve; leaves along the same path in 160ms |
| Agenda event drop (desktop) | the block lands where it was dropped at once (optimistic store update); the server's row replaces it, or it snaps back on error |
| Top bar hairline | transparent at the top of the page, fades in over 200ms once content scrolls under the bar |
| Theme toggle | colours cross-fade over 280ms (`html.theme-switching`) instead of snapping |
| Tap feel | `touch-action: manipulation` and no tap highlight on every button and link; feedback on :active, so on the press, never on release |
| Load gate reveal | content opacity 280ms ease-out plus translateY(6px) to 0 over 320ms on the spring curve; figure mark spins one turn per 1.6s on an ease-in-out, static under reduced motion |
| Agenda suggestions | ghost blocks enter with opacity and translateY(6px) scale(0.98) over 320ms on the spring curve; the tray card slides down 6px; none under reduced motion |
| Agenda event drag | press and hold an event (mouse or pen), a 4px threshold turns it into a drag; the block dims to 45% and a ghost in the info tint follows the pointer in 15 minute steps across days; the bottom 7px is a resize grip; release writes the new times and a toast confirms |
| Tracker tick | background-color 160ms, mark scale(0.9) to 1 in 120ms |
| Widget card hover and press | box-shadow and border-color 160ms ease-out on fine pointers; press scale(0.995); none under reduced motion |

No keyframes on rapidly triggered elements except the skeleton shimmer. Type tracking follows size: h1 -0.02em, h2 -0.012em, h3 -0.008em, body 0, `.small` +0.006em, `.xs` +0.02em.

## 10. Do not change

Route names and paths; nav labels; the `NAV` array; any job; `HOUR_PX` and the click math in AgendaGrid (the drag selection added on 2026-09-15 builds on it and snaps to 15 minutes); the `onEmptyClick` guard; `window.prompt` and `window.confirm` call sites (inline confirm patterns are a logic change, listed in docs/V2.md); form field names; the eight priority, category and status vocabularies; area and mail account colours from the database; the logo files.
