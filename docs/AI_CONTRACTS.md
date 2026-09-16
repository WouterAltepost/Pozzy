# AI contracts

Function signatures in `api/app/integrations/claude_client.py`. Streams A and B define what they need here; stream D implements. Every function returns `None` when AI is off, the call fails, or the answer does not validate, and the caller then uses its deterministic fallback. Callers must also survive an exception.

## Stream A

### Standing rules (`claude_client.standing_rules_block`)

Settings `ai_rules` (list of sentences) and `ai_context` (free text), edited in Settings under "Rules for Pozzy". `_call` puts them at the top of the system prompt of every feature as "## Standing rules from the user" and "## About the user", followed by "## Task instructions" and the feature's own text; the block calls them hard constraints that win over every preference below. The planner also repeats them as `rules` in the user payload and requires a `rule_check` line per item before the pick. Empty when he wrote none. The planner honours a skip: `plan_week` may answer option -1 for an item and the caller drops it. Deterministic paths do not read the rules; hard limits for those live in the structured settings (working window, targets).

### `rank_slots(task: dict, candidates: list[dict], context: dict | None) -> list[dict] | None`

Caller: `api/app/modules/tasks/scheduling.py::suggest_slots`. Kill switch: `ai_enabled.scheduling`. Model: smart.

Input `task`: `Task.to_dict()` (title, description, area_id, tags, urgent, important, due_date, estimated_minutes).
Input `candidates`: at most 12 slots, all already free, deterministic pre-ranked:
```json
[{"start": "2026-09-14T08:00:00+02:00", "end": "2026-09-14T09:30:00+02:00", "day_label": "Mon 14 Sep", "reason_hints": ["morning", "today", "gap_start", "long_gap"]}]
```
Input `context`: `{"limit": 3}`.

Output: ordered list of at most `limit` items, each `{"start", "end", "reason"}` where `start`/`end` are copied verbatim from a candidate and `reason` is one short sentence. The caller drops any item whose start/end pair is not in `candidates` (rule 7: Claude never invents a slot). Fallback: `scheduling/free_slots.py::rank_slots_deterministic` (due date side first, earlier day, morning, gap start, one slot per day).

### `suggest_dos(candidates: dict, context: dict | None) -> list[dict] | None`

Caller: `api/app/modules/dos/service.py::suggest_dos`. Kill switch: `ai_enabled.three_dos`. Model: smart.

Input `candidates`:
```json
{
  "date": "2026-09-15",
  "tasks": [{"id": "...", "title": "...", "quadrant": "do", "due_date": "2026-09-16", "area": "Work", "estimated_minutes": 60}],
  "deadlines": [{"id": "...", "title": "...", "course": "...", "due_at": "2026-09-18T23:59:00+02:00", "task_id": "..."}],
  "weekly_goals": [{"id": "...", "title": "...", "area": "Study", "done": false}],
  "rolled_over": [{"title": "...", "rolled_from_date": "2026-09-14"}]
}
```
Input `context`: `{"count": 3}`.

Output: list of at most `count` items `{"title": str, "task_id": str | null, "reason": str}`. `task_id`, when set, must be one of `candidates.tasks[].id` or `candidates.deadlines[].task_id`; the caller drops others. Fallback: deterministic pick in `dos/service.py` (rolled over do's first, then due today or overdue, then quadrant `do`, then nearest deadline).

## Stream C

### `classify_emails(batch: list[dict]) -> list[dict] | None`

Caller: `api/app/services/mail_classify.py::call_claude`, from the `mail_sync_and_classify` job and `POST /api/mail/emails/<id>/reclassify`. Kill switch: `ai_enabled.mail_classify` (the caller checks it too and skips the call when off). Model: fast (Haiku). Batch size: at most 15 (Settings `mail_classify_batch`). Use prompt caching for the system prompt.

Input `batch`, one item per email, `snippet` is at most 1200 characters of the stored 2 KB snippet:
```json
[
  {
    "id": "6f1c...-uuid",
    "account_label": "Work",
    "from_name": "Alice Example",
    "from_email": "alice@client.com",
    "subject": "Invoice question",
    "date": "2026-09-14T10:15:00+02:00",
    "snippet": "Hi Wout, could you send the invoice for August? Thanks, Alice"
  }
]
```

Output: a list with one item per input id (missing ids are fine, they fall back to rules):
```json
[
  {
    "id": "6f1c...-uuid",
    "priority": 2,
    "category": "client",
    "area": "Work",
    "needs_reply": true,
    "one_line_summary": "Alice asks for the August invoice."
  }
]
```

Field rules, enforced by the caller (`validate_item`), an item failing any of them is dropped and that email uses the rule fallback:
- `id`: must be one of the input ids. Unknown ids are dropped.
- `priority`: integer 1 (urgent), 2 (important), 3 (normal), 4 (low or noise).
- `category`: one of `client`, `school`, `finance`, `personal`, `newsletter`, `notification`, `other`.
- `area`: one of `Study`, `Work`, `Personal`, `Health`, or `null`. Any other string is treated as `null`.
- `needs_reply`: boolean.
- `one_line_summary`: non-empty string, one sentence, the caller trims it to 300 characters.

Fallback: `mail_classify.classify_rules` (priority 3, or 4 for newsletter and notification; category from sender and subject heuristics; area from category; `needs_reply` false; summary is the subject). The caller writes only the raw columns `priority`, `category`, `area_id`, `needs_reply`, `summary`, `classifier` (`claude` or `rules`) and `classified_at`; manual overrides live in `priority_override`, `category_override`, `area_override_id` and are never written by classification.

## Stream D (own functions)

All implemented in `api/app/integrations/claude_client.py` through one helper `_call` that checks the kill switch, resolves the model tier, renders `api/app/prompts/<name>.md` (linked from `docs/prompts/`), parses JSON, validates with pydantic, writes `ai_calls`, and returns `None` on any failure. Prices are hardcoded in `PRICES` there. Under `TESTING` the client is never built; tests inject a fake via `app.extensions["pozzy_anthropic"]` (see `api/tests/d/conftest.py`).

### `parse_capture(payload: dict) -> dict | None`

Caller: `modules/captures/service.py::build_proposal`. Kill switch: `ai_enabled.capture`. Model: smart. Prompt `capture_parse`.

Input: `{"text", "today", "weekday", "timezone", "areas": [names], "trackers": [{"name", "type", "unit"}], "courses": [names]}`.
Output: `{"type": "task|event|goal|note|tracker", "confidence": 0..1, "reason": str, "fields": {...}}`. The `fields` sub-object per type is defined by the pydantic models in `modules/captures/schemas.py` (`TaskFields`, `EventFields`, `GoalFields`, `NoteFields`, `TrackerFields`); the caller re-validates against them and falls back to `parse_deterministic`.

### `write_briefing(context: dict) -> str | None`

Caller: `modules/ai/briefing.py::generate_briefing`. Kill switch: `ai_enabled.briefing`. Model: smart. Prompt `daily_briefing`.

Input: the dict from `briefing.build_context(day)` (dos, tasks_due, scheduled_tasks, events, deadlines, application_steps, weekly_goals, trackers_open, hours, emails, yesterday). Output: the briefing text (plain, paragraphs separated by blank lines). Fallback: `briefing.deterministic_text`.

### `reply_briefing(payload: dict) -> dict | None`

Caller: `modules/ai/briefing.py::add_note` (reply box under the briefing). Kill switch: `ai_enabled.briefing`. Model: smart. Prompt `briefing_reply`.

Input: `{"date", "weekday", "briefing" (current text), "previous_notes": [str], "note": str, "context": build_context(day) plus "notes", "candidates": {"emails": [{id, from, subject}], "tasks": [{id, title, due_date}], "areas": [names]}}`. Output: `{"reply": str, "text": str (the rewritten briefing), "actions": [{"type", ...ids or fields, "reason"}]}` with `type` in `mark_email_handled | complete_task | drop_task | add_do | add_note | set_hour_target`. `briefing.validate_actions` keeps only actions whose ids and area names come from `candidates`, caps at six, and attaches a `label` and `index`. Actions are stored on the note with `applied: false`; `POST /api/ai/briefing/notes/<i>/apply` runs the ticked ones through the owning services (mail `update_email`, tasks `complete_task`/`update_task`, dos `create_do`, notes `create_note`, the `hour_targets` setting). Fallback: the note is stored, the deterministic text gains a "Your note:" line, no actions. Notes are passed as `context.notes` to every later `write_briefing` for the same day.

### `plan_week(payload: dict) -> dict | None`

Caller: `modules/ai/planner.py::build_plan` (the Plan button on the Agenda page, `POST /api/ai/plan` with `{start, days}`). Kill switch: `ai_enabled.scheduling`. Model: smart. Prompt `plan_week`.

The planner is deterministic first: open unscheduled tasks (by due date and quadrant, max 8), upcoming study deadlines (prep block of 90 minutes before the due time, max 3) and this week's unmet goals (60 minute block, max 3) are placed greedily into free working slots from `scheduling/free_slots.py`, at most three per day, with every accepted placement added to the busy set. Each item keeps up to three ranked options. Busy intervals are widened by Settings `plan_buffer_minutes` on both sides (the same buffer applies to single-task slot suggestions). Input to Claude: `{"week_of", "items": [{id, kind, title, minutes, why, options: [{index, start, end, day_label, hints, before, after}]}]}` where `before` and `after` are the appointments around the option on that day (`title`, `location`, `ends` or `starts`, `gap_minutes`), so the standing rules about travel and buffers can be checked; `after` and `before` include task-linked events. Output: `{"items": [{"id", "option", "reason"}]}`. The caller applies only indexes that exist, drops a pick that would overlap an earlier pick, and keeps the deterministic option and reason otherwise (rule 7). Nothing is written: the response lists suggestions with stable ids (`task:<id>`, `event:<deadline or goal id>`) and the client accepts each through `POST /api/tasks/<id>/schedule` or `POST /api/calendar/events`. Fallback: the deterministic plan with rule-based reasons.

### `review_week(stats: dict, max_goals: int = 5) -> dict | None`

Caller: `modules/reviews/service.py::generate_review`. Kill switch: `ai_enabled.weekly_review`. Model: smart. Prompt `weekly_review`.

Input: the snapshot from `services/review_stats.py::compute(week_start)`. Output: `{"reflection": str, "next_week_focus": [{"title", "area", "target_value", "task_id", "reason"}]}`; `task_id` is kept only when it is one of `open_task_candidates[].id` or `deadlines.upcoming[].task_id`. Fallback: `deterministic_reflection` and `deterministic_focus` in the same service.

### `classify_emails(batch: list[dict]) -> list[dict] | None` (stream C's contract)

C's contract lives in this file on branch `stream/C-mail` (read from that worktree on 2026-09-14, not yet pushed); E merges the two sections. Implemented as C specified: chunks of `mail_classify_batch` (max 15) on the fast model, system prompt marked `cache_control: ephemeral`, every item validated (id in batch, priority 1 to 4, category in the list, area in the four names or null, non-empty summary), duplicates dropped. Returns the results of every chunk that succeeded and `None` only when no chunk did. Note: Haiku 4.5 needs a 4096-token prefix before caching engages, so `cache_read_input_tokens` stays 0 until the system prompt grows past that; the marker is harmless.
