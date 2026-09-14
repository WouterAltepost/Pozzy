# AI contracts

Function signatures in `api/app/integrations/claude_client.py`. Streams A and B define what they need here; stream D implements. Every function returns `None` when AI is off, the call fails, or the answer does not validate, and the caller then uses its deterministic fallback. Callers must also survive an exception.

## Stream A

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
