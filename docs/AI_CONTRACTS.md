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
