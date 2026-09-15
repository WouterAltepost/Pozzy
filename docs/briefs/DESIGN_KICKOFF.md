# Pozzy design pass: kickoff prompt for Claude Code

Paste everything below this line into a Claude Code session started in ~/Desktop/Projects/Pozzy on main.

---

You are running the UI design pass for Pozzy, my personal operating system dashboard. v1 is released and running in production; it is functionally complete but the frontend is deliberately plain CSS with no design. Your job is to give the existing app a real, consistent visual design without changing any behaviour.

## What I am building

The design for the existing Pozzy web app (web/), a Vue 3 + Vite PWA: the top bar with CaptureBar, the navigation, the homepage widget grid, and all twelve routes (Homepage, Agenda, Mail, Tasks, Goals, Trackers, Hours, Capture, Study, Notes, Weekly Review, Settings). Single user, used mostly on a laptop at a desk, secondary use on an iPhone (390px) as an installed PWA.

## Read first, in this order

1. CLAUDE.md. Note: its rule "plain CSS, no design work in v1" is explicitly overridden for this session. Every other rule still applies.
2. docs/POZZY_PLAN.md section 6 (what every view shows) and docs/ROUTES.md and docs/WIDGETS.md (the full list of screens and homepage widgets, with widget order). These enumerate everything the design must cover.
3. docs/PROGRESS.md "v1 released" section (known gaps and per-stream decisions) and docs/briefs/BUILD.md (how views and widgets are organised and who owned which files).
4. web/src/: App.vue (top bar and nav), styles/base.css (the only shared stylesheet), views/*View.vue, components/home/*Widget.vue, components/agenda/*, components/mail/*, components/settings/*, components/CaptureBar.vue, router/index.js.
5. Branding/: pozzy-svg.svg and pozzy.png (logo), favicon-svg.svg, Group.png (wordmark). These are final artwork. Embed them as assets exactly as they are. Never redraw, restyle, recolour or "improve" them.
6. Inspo/: three screenshots. They are reference for mood, density and feel only, not something to copy. One consistent direction, derived from the logos, is the goal.

## Skills to use, in this order

Before using any skill, read its SKILL.md so you know exactly what it needs (tools, API keys, network). If a skill cannot run in this environment, stop and tell me instead of improvising a substitute.

1. /impeccable: read this brief, the logos and the Inspo screenshots and set the design direction. Treat the screenshots as mood and density reference, not a template.
2. /brandkit: derive the palette, type pairing and spacing scale from the logos before any layout work. Output the result as CSS custom properties (tokens) because that is how the design will be implemented.
3. /high-end-visual-design is the quality bar and /design-taste-frontend is the guard against templated layouts. Do not use minimalist-ui, industrial-brutalist-ui or gpt-taste; I want one consistent direction.
4. /imagegen-frontend-web: before writing any UI or the design brief, generate one reference image per section and show them to me. Sections: Homepage (widget grid with top bar, nav and CaptureBar), Agenda (week view plus event editor), Mail (unified inbox list plus message detail), Tasks (Eisenhower board), Goals and Trackers (weekly goals, daily three do's, tracker chart), and one component sheet (buttons, inputs, cards, badges for priority, quadrant and life area, empty states, light and dark). If you think a different split serves the app better, say so before generating. Then STOP and wait for my OK or feedback. Do not write the brief or touch code before I approve.
5. Only after my OK: write docs/briefs/DESIGN.md, then apply it (see below).
6. /animate for every transition and hover state, /apple-design for anything gesture or spring based (drag and drop on the Eisenhower board and application kanban, the mobile nav, sheet-style editors). Run /review-animations on the result before showing it to me.

## Decisions to propose at the image gate

Present these with the reference images so I can decide everything in one go. Give a recommendation and a one-line reason for each:

- Light only, dark only, or both (following system preference).
- Information density: airy vs compact, given the inspo.
- Implementation: plain CSS custom properties and shared components (current stack, no new dependency) versus adding a library such as Tailwind or a headless component library. Default recommendation is plain CSS tokens unless you have a strong reason.
- Desktop first with a 390px mobile pass, or mobile first.
- Any colour rules implied by the logo (for example whether the logo colour may be used as the accent for interactive elements, or should stay reserved for branding).
- Fonts: system stack or a self-hosted webfont pair. If webfont, it must be bundled locally, no runtime request to Google Fonts.

## What DESIGN.md must contain

Precise enough that the implementation needs no further questions:

- Tokens as CSS custom properties: colours (light and dark), type scale, spacing scale, radii, shadows, motion durations and easings, z-index layers.
- Typography rules and the font loading approach.
- Component specs with all states (default, hover, focus, active, disabled, loading, empty, error): buttons, inputs and selects, cards, widget frame, badges for priority, Eisenhower quadrant and life area (Study, Work, Personal, Health), nav and top bar with CaptureBar, modals and sheets, toasts, tables and lists, the inline SVG tracker chart, drag and drop affordances.
- Per-view layout for all twelve routes, plus the homepage grid with the widget order from docs/WIDGETS.md, at desktop and at 390px.
- Dark mode rules, focus visibility and contrast (WCAG AA), reduced-motion behaviour.
- PWA: icons and manifest theme and background colours derived from the logo, favicon from favicon-svg.svg.
- Motion spec per transition and hover state.
- A "do not change" list (below).

## Hard constraints

- No API changes, no store (Pinia) changes, no router changes, no logic changes, no data model or DB changes. This is presentation only. If a design needs a logic change, note it in docs/V2.md instead of doing it.
- All 208 backend tests must stay green (pytest in api/). npm run build must pass. The web Railway build command is just npm run build; do not reintroduce npm ci.
- Shared components and tokens, never per-view one-off styling. Views were built by four different streams and have small markup and class inconsistencies; normalise them through shared components as you go.
- Never use long dashes (em or en dashes) in any file, commit message or output. Use commas, colons or plain hyphens.
- Secrets live only in the root .env. Never touch .env.example beyond placeholders. Do not touch DB config or the Supabase pooler settings.
- Do not modify anything under api/ except when a test fixture references a changed asset path, and say so if you do.

## Verification before you report

1. pytest in api/ (208 green) and npm run build in web/.
2. Click through every one of the twelve routes plus the login screen with Playwright at 1440px and at 390px, light and dark, and save screenshots to docs/design-screens/. Check no horizontal scroll at 390px, all interactive elements reachable by keyboard, focus visible.
3. /review-animations on all motion.
4. Commit in small logical commits (tokens, shared components, per-view passes, motion, PWA assets). Do not deploy until I have seen the screenshots and said go; then push to main so Railway deploys, and confirm the production URL renders.
5. Update docs/PROGRESS.md with a "Design pass" section: what changed, decisions taken at the image gate, anything deferred to docs/V2.md.

## Where to pause for me

Only at three points: after the reference images (step 4), after the screenshots and animation review (before deploy), and if a skill or tool cannot run in this environment. Everywhere else, decide and continue.
