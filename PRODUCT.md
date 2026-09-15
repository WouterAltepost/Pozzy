# Product

<!-- impeccable:product-schema 1 -->

Inferred from docs/briefs/DESIGN_KICKOFF.md, docs/POZZY_PLAN.md and CLAUDE.md on 2026-09-15; no interview was held (the design brief allows decisions outside its three pause points). Facts marked [inferred] were not confirmed by the owner.

## Platform

web

## Users

One user: Wouter Altepost, solo developer and student, founder of alpaca AI and UDefine. He runs his week from Pozzy: mostly at a desk on a laptop, secondarily on an iPhone (390px) as an installed PWA. [inferred] Typical sessions: a morning check of do's, agenda, mail and deadlines; short check-ins during the day (tick a tracker, log hours, capture a thought); an evening planning pass setting tomorrow's three do's.

## Product Purpose

A private personal operating system: calendar (iCloud), mail triage (four Google accounts, read-only), tasks (Eisenhower), weekly goals and daily three do's, habit tracking, hours per life area, study deadlines and internship applications, notes, quick capture, and a weekly review. Claude is used only where judgement helps (email priority, slot ranking, briefing, capture parsing, reflection). Success: Wouter uses it for a full day with no manual edits and knows within seconds what today needs.

## Positioning

Everything Wouter needs to run a week in one screen, with AI as an assistant that ranks and drafts but never invents: free slots are computed, Claude only orders them; do's roll over automatically; mail is triaged into one inbox but never touched on the server.

## Operating Context

- Life areas: Study, Work, Personal, Health. Each has a colour stored in the database (areas table), used as data colour throughout.
- Timezone Europe/Amsterdam, week starts Monday, UI in English.
- Twelve routes: Home, Agenda, Tasks, Goals, Mail, Tracking, Hours, Capture, Study, Notes, Review, Settings. Route names and paths are fixed (docs/ROUTES.md).
- Homepage is a grid of ten self-contained widgets in a fixed order (docs/WIDGETS.md).
- Background jobs sync calendar and mail every 10 and 15 minutes; the UI must be honest about "not synced yet" and job failures (Settings shows job runs).

## Capabilities and Constraints

- Vue 3 + Vite PWA, plain CSS, Pinia, Vue Router. Flask API. Supabase Postgres and Auth.
- Design pass constraint (2026-09-15): presentation only. No API, store, router, logic, data model or DB changes. Shared components and tokens, never per-view one-off styling.
- Mobile: every view usable at 390px, no horizontal scroll.
- No em or en dashes anywhere (files, commits, UI copy).
- Webfonts must be bundled locally; no runtime request to Google Fonts.
- Recurring iCloud occurrences are read-only; the hours timer lives in the browser; quick-add has no Claude parsing (docs/V2.md).

## Brand Commitments

- Name: Pozzy. Logo: a hand-inked red hub with eight spokes ending in rings, three of them filled. Wordmark: classical Roman capitals "POZZY".
- Assets in Branding/ are final and must be embedded exactly as they are, never redrawn, restyled or recoloured: pozzy.png and pozzy-svg.svg (mark plus wordmark), favicon-svg.svg (mark), Group.png (mark, raster).
- Asset discrepancy found on 2026-09-15: favicon-svg.svg, pozzy.png and Group.png are red (#AF1616 in the SVG, #A81010 sampled from the PNGs) while pozzy-svg.svg carries fill #2E7338 (green). Treated as an export error at the time. On 2026-09-15 Wouter asked for the mark to become galaxy blue (#2A4B7C); the SVG was recoloured at source and the PNGs by hue mapping, so every asset in web/public is blue now while the Branding folder keeps the originals. [confirmed]
- Inspo/ screenshots (three SaaS dashboards) are references for mood and density only.

## Evidence on Hand

- Real data in production: 61 calendar events, 355 classified emails, a daily briefing, job runs. Screens can be verified against real content; no synthetic content is needed.
- No testimonials, pricing or marketing surface exist and none may be invented; the app has no public page beyond login.

## Product Principles

1. The task is the interface: every screen answers "what needs my attention now" before anything else.
2. Honest state: synced, not synced, failed, empty and loading are all visible and specific.
3. One vocabulary: the same button, input, badge and card everywhere; brand lives in details, not decoration.
4. Data colour is data: area colours and mail account colours come from the database and are never restyled; the brand red is reserved for identity and the "now" marker.
5. Works without AI and without integrations; the design never depends on a Claude call or a sync to look complete.

## Accessibility & Inclusion

WCAG AA contrast in light and dark, visible keyboard focus on every control, reduced-motion behaviour for every transition. Single user, no localisation beyond English.
