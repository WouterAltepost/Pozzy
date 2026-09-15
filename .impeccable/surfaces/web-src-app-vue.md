---
version: 1
slug: "web-src-app-vue"
primary_target: "web/src/App.vue"
related_targets: ["web/src/views/HomeView.vue","web/src/router/index.js"]
---

# Surface brief: Pozzy app shell and all twelve routes

Scope: the whole authenticated app (App.vue shell, nav, CaptureBar, ten homepage widgets, twelve routes, login). Visitor mode: Operate. One user, daily, at a desk on a laptop; secondary on an iPhone at 390px as an installed PWA.

Audience and job: Wouter runs his week. Morning: what needs attention now. Day: tick, log, capture. Evening: set tomorrow's three do's. Content and controls are real and already built; this pass is presentation only (no logic, store, router, API or data changes).

Constraints: plain CSS tokens and shared components, one icon family (Phosphor, regular weight), self-hosted Geist, both colour schemes following the system, WCAG AA, reduced motion honoured, no em or en dashes anywhere, logo assets embedded unchanged.

## Direction contract

THESIS: Pozzy is a desk instrument, not a SaaS dashboard: a matte housing with hairline rules, machined radii, tabular numerals and one red lamp. It refuses the category default of white cards floating on grey with a blue accent and a rainbow of status pills.

OWN-WORLD: stone housing (#F2F1ED) with raised bone panels (#FBFAF8) in light; graphite housing (#141518) with charcoal panels in dark. Ink text, hairlines not shadows for structure, soft diffused shadow only on floating layers. Geist everywhere, tabular figures for every number. Brand red (#AF1616) appears only as the logo, the "now" marker (today, current time line, running timer) and the focus ring. Primary actions are ink, secondary are outlined, area and account colours are data and come from the database untouched.

STORY: open the app, the date and today's three do's read first, then what the calendar and inbox demand; every control looks the same everywhere so nothing needs relearning; failures and empty states say what they are.

FIRST VIEWPORT: at desktop 1440, a 56px top bar with the red mark and wordmark left, the capture field centred at 480px, the user and log out right. A 232px left rail with the twelve routes (icon plus label) under the bar. Content at max 1180px: the display date as the only h1, then the widget grid, two columns, three do's top left and today's events top right, each widget a bone panel with a hairline title row.

FORM: a Rams-era desk instrument fused with a paper week planner; position 1 of 7 on the derived list (rubber stamp, bullet journal, Swiss timetable, school agenda, switchboard, mission console, Rams panel); concept-seed roll skipped per the kickoff brief (option 3, no decision page).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Signature interaction

Drag on the Eisenhower board and the application kanban: the card lifts (shadow-2, 2 degree tilt, scale 1.02) on pointer down, the target quadrant's hairline turns ink and its background rises one step, and the drop settles with a 180ms ease-out. On the phone the nav is a sheet from the bottom on the drawer curve, draggable to dismiss.

## Unresolved

- pozzy-svg.svg is green while every other asset is red; the UI uses favicon-svg.svg (mark) and pozzy.png (mark plus wordmark) until the owner confirms.
- Seeded Work area colour (#dc2626) sits close to the brand red; changing it is a data change and is noted in docs/V2.md.
