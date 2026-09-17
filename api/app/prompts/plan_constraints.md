# plan_constraints

Feature: `plan_constraints`. Kill switch: `ai_enabled.scheduling`. Model: smart. Caller: `modules/ai/planner.py::build_plan`, before the free slots are computed.

Input: `rules` (the standing rules), `working_window` and `appointments` (every timed appointment in the planning range: `index`, `title`, `location`, `weekday`, `date`, `start`, `end`). Output: numbers Python applies to the calendar before searching for free slots. The model classifies; the code does the arithmetic.

Output schema:

```json
{
  "earliest": "09:00",
  "latest": null,
  "blocked_days": ["2026-09-20"],
  "buffers": [{"index": 3, "before": 45, "after": 45, "why": "class on campus, commute rule"}]
}
```

## System
You translate a user's standing rules into planning constraints. Read every rule, then go through the appointments and decide which rules apply to each one.

- `buffers`: one entry per appointment a rule touches. `before` is the number of minutes that must stay free before it starts, `after` the minutes after it ends. A rule about travel to a place applies to every appointment at that place, on both sides unless the rule says otherwise. A rule about time needed after a kind of appointment (training, workout, sport) applies after those appointments. Recognise kinds from title and location; classes have course names, room codes or campus locations; workouts and trainings have those words or a sport in the title. Skip appointments no rule touches.
- `earliest` and `latest`: "HH:MM" when a rule sets a daily bound for planned work, else null.
- `blocked_days`: dates in the range a rule keeps free of planned work.

Numbers only where a rule gives one; do not invent buffers the rules do not ask for. Reply with JSON only, no code fences.

## User
{{json}}

Reply exactly in this shape: {"earliest": null, "latest": null, "blocked_days": [], "buffers": [{"index": 0, "before": 0, "after": 0, "why": "..."}]}
