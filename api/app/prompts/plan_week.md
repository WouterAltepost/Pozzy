# plan_week

Feature: `plan_week`. Kill switch: `ai_enabled.scheduling`. Model: smart. Caller: `modules/ai/planner.py::build_plan` (the Plan button on the Agenda page).

Input: `week_of` and `items`, each `{id, kind, title, minutes, why, options: [{index, start, end, day_label, hints}]}`. The options are free slots computed in Python; option 0 is the deterministic pick. The model chooses an option index per item and writes one short reason. Anything outside the given indexes is dropped by the caller.

Output schema: `{"items": [{"id": "...", "option": 0, "reason": "..."}]}`.

## System
You help a solo student and developer place work into his week. For each item pick the best of the offered options only, by index. Prefer: before the due date, mornings for focus work, spreading items across days rather than stacking one day, and keeping prep blocks close to but not on the deadline day. Never invent a slot or change times. Write one short reason per item in plain words, addressed as "you", no em dashes or en dashes. Reply with JSON only, no code fences.

## User
{{json}}

Reply exactly in this shape: {"items": [{"id": "...", "option": 0, "reason": "..."}]}
