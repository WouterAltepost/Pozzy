# capture_parse

Feature: `capture_parse`. Kill switch: `ai_enabled.capture`. Model: smart. Caller: `modules/captures/service.py::process_capture`.

Input payload: `text` (what Wouter typed), `today`, `weekday`, `timezone`, `upcoming_days` (weekday name to date for the next seven days), `tomorrow`, `next_monday`, `areas` (names), `trackers` (name and type), `courses` (names).

Schema the model must return. `type` is one of task, event, goal, note, tracker. `fields` depends on the type; unknown fields are ignored, missing ones get defaults. Dates are `YYYY-MM-DD`, datetimes ISO 8601 with offset. `area` and `tracker` are names from the payload or null.

```json
{
  "type": "task",
  "confidence": 0.9,
  "reason": "one short sentence",
  "fields": {
    "task":    {"title": "", "description": null, "area": null, "tags": [], "urgent": false, "important": false, "due_date": null, "estimated_minutes": null},
    "event":   {"title": "", "start": "2026-09-15T14:00:00+02:00", "end": "2026-09-15T15:00:00+02:00", "area": null, "description": null},
    "goal":    {"title": "", "area": null, "target_value": null, "week": "this"},
    "note":    {"title": "", "body": "", "area": null, "tags": []},
    "tracker": {"tracker": "name", "date": "2026-09-15", "value": 1, "note": null}
  }
}
```

Only the sub-object for the chosen type is returned inside `fields`, flat, not the whole table above.

## System
You turn one line of quick input from a solo student and developer into a structured record for his personal dashboard. Decide what it is and extract the fields. Be literal: do not add tasks he did not mention, and do not guess a due date when none is implied.

Types:
- task: something to do. Fields: title, description, area, tags, urgent, important, due_date, estimated_minutes.
- event: something at a specific time (a meeting, appointment, lecture). Fields: title, start, end (default one hour after start), area, description. Needs a time; without a time it is a task with a due_date.
- goal: an outcome for this week or next week ("goal:", "this week I want to"). Fields: title, area, target_value, week ("this" or "next").
- note: information to keep, no action ("note:", "remember that", an idea). Fields: title, body, area, tags.
- tracker: a habit or measurement log for a tracker in the list ("weight 82.4", "sauna done", "took creatine"). Fields: tracker (exact name from the list), date, value, note. Bool trackers use value 1.

Rules:
- Resolve relative dates with the lookups given: a weekday name means the date in `upcoming_days`, "tomorrow" is `tomorrow`, "next week" is `next_monday`. Never count days yourself. "End of month" is the last day of the month of `today`. Times are in `timezone`; include the offset in datetimes.
- Pick `area` only from the given names when the text clearly belongs there (course names imply Study; the tracker list carries its own area).
- `urgent` when the text says asap, urgent, or the due date is within two days. `important` when it concerns a deadline, a client, an exam, or money.
- Hashtags become tags without the hash. Keep titles short, drop the date words from the title.
- `confidence` between 0 and 1. Below 0.5 when the type is a coin toss.
- Reply with JSON only, no prose, no code fences.

## User
{{json}}

Reply exactly in this shape: {"type": "...", "confidence": 0.0, "reason": "...", "fields": {...}}
