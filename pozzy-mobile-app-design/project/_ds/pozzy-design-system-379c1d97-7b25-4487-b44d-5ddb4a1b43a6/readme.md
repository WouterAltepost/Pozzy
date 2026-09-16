# Pozzy Design System

Pozzy is Wouter Altepost's personal operating system: one private web app (Vue 3 PWA + Flask API) that runs his week from a single dashboard. Twelve fixed routes: Home, Agenda (iCloud), Tasks (Eisenhower), Goals (weekly goals + daily three do's), Mail (four Google inboxes, read-only triage), Tracking (habits), Hours (time per life area), Capture, Study, Notes, Review, Settings. One user, desk-first on a laptop, secondarily an iPhone PWA at 390px. Claude ranks and drafts; it never invents.

Direction in one line (from docs/briefs/DESIGN.md): "a desk instrument, not a SaaS dashboard. A matte stone housing carries raised bone panels separated by hairlines; numbers are tabular; one red lamp marks now."

## Sources

- GitHub: https://github.com/WouterAltepost/Pozzy (branch main). Tokens and base styles: `web/src/style.css`. Spec: `docs/briefs/DESIGN.md`, `PRODUCT.md`, `docs/WIDGETS.md`, `docs/ROUTES.md`. Components: `web/src/components/ui/*.vue`, `web/src/components/{home,mail,tasks,agenda,shared}/`. Branding: `Branding/`. Reference renders: `docs/design-screens/*.png` (four copied to `reference/`).
- Explore the repo for pixel-exact values before building new screens; every value here was lifted from it.

## Content fundamentals

- Voice: second person, plain, direct, no marketing. Sentences state facts: "Nothing due", "Inbox handled", "No events today", "Nothing on the calendar mirror for today."
- Sentence case everywhere, including titles: "Today's three do's", "Due today or overdue", "Hours this week". Buttons are verbs: "Sync now", "New task", "Set three do's", "Regenerate", "Confirm", "Discard".
- Empty and error states are specific and honest: "No mail accounts are configured (MAIL_ACCOUNTS_JSON)." Sync results are numeric: "Synced: 12 new, 9 classified (haiku). Failed: UDefine."
- No em or en dashes anywhere. Use a comma, a colon or "to" ("09:30 to 12:00").
- Dates en-GB: "Tue 15 Sept", "Week of Mon 15 Sept"; 24h times; week starts Monday; timezone Europe/Amsterdam. Money "$0.544".
- Numbers that can be compared are tabular (`.num`). Counts are phrased as prose: "3 of 5 done", "12 open", "2 unhandled, 1 need a reply".
- Badges are lowercase single words: reply, task, linked, scheduled, inbox, rolled 2x. Priorities P1..P4 (Urgent, Important, Normal, Low or noise).
- No emoji. No exclamation marks. UI text is English even though the data is often Dutch.

## Visual foundations

- Colour: warm stone housing `--bg #F2F1ED`, bone panels `--surface #FBFAF8`, insets `--surface-2`, pressed `--surface-3`. Three ink levels. Brand red `#AF1616` is reserved for the logo, the today column and now line, the running timer and the focus ring; it is never a button. The interactive accent is ink: primary buttons are `--ink` fill with `--on-ink` text. Semantic ok/warn/danger/info each with a soft tint for badges. Life-area colours (Study #2563eb, Work #dc2626, Personal #059669, Health #d97706) and mail-account colours come from the database and are data, never decoration; tints via `color-mix(in srgb, var(--area) 14%, transparent)`.
- Dark mode follows the system; `data-theme` forces it. Same token names, shadows go to alpha 0.5 to 0.7.
- Type: Geist variable only, self-hosted (`assets/fonts/geist-latin.woff2`). Base 14px/1.5. Scale 11, 12, 13, 14, 16, 18, 22, 28. Weights 400 body, 500 labels and buttons, 600 titles. Titles track -0.01em, the 28px home date -0.02em, 11px labels +0.02em. The serif exists only inside the logo image.
- Spacing: 4px base, sp-1..sp-10. Cards pad sp-4 (sp-5 from 900px), widget grid gap sp-5, rows pad sp-2 vertical.
- Radii: 6 badges and tags, 8 controls and task cards, 12 cards and popovers, 16 sheets, pill for chips and nav items.
- Cards: surface, 1px `--line` hairline, r-lg, shadow-1. Never nested; grouping inside is a `--surface-2` inset. Selected rows get an ink border plus 1px inset ring.
- Shadows are faint and ambient: shadow-1 on cards, shadow-2 on popovers and lifted drag cards, shadow-3 on sheets and toasts.
- Backgrounds: flat colour only. No images, gradients, textures or illustrations. The top bar is `--surface` at 88% with `blur(14px) saturate(160%)`; that is the only transparency and blur.
- Borders: hairlines separate everything (rail, top bar, rows, table cells). Inputs use `--line-2`. Quadrants use a 2px top rule in the quadrant colour; agenda events use a 3px left colour bar.
- Motion: only transform, opacity, colour and shadow. Press scale(0.97) 120ms; hover colour 160ms gated to fine pointers; popovers scale 0.97 to 1 in 200ms; side panels slide 8px in 240ms; sheets slide up on ease-drawer 420ms with drag-to-dismiss; toasts rise 8px. Skeleton shimmer 1.6s. No route transitions. Reduced motion collapses to opacity and colour.
- Hover: buttons darken one step (ink to ink-2, surface to surface-2); rows and cards get `--line-2` border plus shadow-1; nav items surface-2. Press: scale 0.97 (0.94 on icon buttons). Focus: 2px brand ring, 2px offset, everywhere.
- Layout: 56px sticky top bar, 232px sticky rail from 1024px, content max 1180px, page padding sp-6. Home is a two-column widget grid from 900px. Side panels (360px) become bottom sheets under 900px. Mobile 390px with no horizontal scroll.
- Imagery: none. The only pictures are the logo files.

## Iconography

- Phosphor Icons, regular weight (`@phosphor-icons/vue` in the app; this system links `@phosphor-icons/web@2.1.1` from unpkg and wraps it in `Icon`). Sizes: 18px nav, 16px buttons and icon buttons, 15px capture bolt, 26px empty states, 14px bold check inside met tracker chips.
- Route icons: house, calendar-blank, check-square, target, envelope-simple, chart-line-up, timer, lightning, graduation-cap, note, clipboard-text, gear-six. Utility: sun, moon, sign-out, list, caret-left, caret-right, tray, check, x.
- The select caret is an inline SVG data URI in base.css. No icon font besides Phosphor, no PNG icons, no emoji, no unicode glyphs as icons.
- Logo: `assets/logo-mark.svg` (mark, favicon), `assets/logo-wordmark.png` (mark + POZZY, login at 180px), `assets/logo-mark.png` (raster, PWA icons). `assets/logo-wordmark-green-unused.svg` is a green export the repo treats as an error; do not use. Embed the logo files as-is; never redraw or recolour.

## Components

Ported from `web/src/components/` (Vue) to React. Inventory follows the repo; `Icon` is the one intentional addition (wrapper for the Phosphor glyph set).

- core/: Button, IconButton, Badge (+ PriorityBadge, Tag), AreaDot, Card (+ Inset), PageHeader, Field, Segmented, ProgressBar, WeekNav, Icon
- feedback/: Empty, Skeleton, Toast, Sheet
- shell/: TopBar, CaptureBar, NavRail (+ NavItem, NAV)
- product/: ListRow, TaskCard (+ Quadrant, QUADRANTS), EmailRow, TrackerChip

Not yet ported (present in the repo): AgendaGrid, EventForm, SyncBar, TaskForm, SlotPanel, ProposalEditor, EmailDetail, MailFilters, LineChart, TrackerForm, TagsInput, AreaSelect, settings account lists.

## Index

- `styles.css` imports `tokens/` (fonts, colors, typography, spacing, elevation, motion, base).
- `guidelines/` foundation cards (Colors, Type, Spacing, Motion, Brand).
- `components/<group>/` React components with `.d.ts`, `.prompt.md` and one card per group.
- `assets/` logo files and the Geist webfont. `reference/` four repo renders (home, agenda, tasks, login).
- `ui_kits/pozzy/` click-through app recreation: Login, Home widget grid, Agenda week grid with editor panel, Tasks Eisenhower board with drag and side panel, Mail list with filters and detail panel. Other routes show a labelled placeholder.
- `SKILL.md`, `github.md`, `thumbnail.html`.
