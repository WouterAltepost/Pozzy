from ...models.task import TASK_SOURCES, TASK_STATUSES
from ...utils.validation import (
    parse_bool,
    parse_date,
    parse_datetime,
    parse_enum,
    parse_int,
    parse_str,
    parse_tags,
    parse_uuid,
    require_object,
)

QUADRANTS = {
    "do": (True, True),
    "schedule": (False, True),
    "delegate": (True, False),
    "eliminate": (False, False),
}


def parse_task_body(body, *, partial: bool) -> dict:
    """Return a dict of validated fields. With partial=True only present keys are returned."""
    body = require_object(body)
    out = {}

    def put(key, value, present):
        if present or not partial:
            out[key] = value

    put("title", parse_str(body, "title", required=not partial, max_len=200), "title" in body)
    put("description", parse_str(body, "description"), "description" in body)
    put("area_id", parse_uuid(body, "area_id"), "area_id" in body)
    put("tags", parse_tags(body, default=[]), "tags" in body)
    put("urgent", parse_bool(body, "urgent", default=False), "urgent" in body)
    put("important", parse_bool(body, "important", default=False), "important" in body)
    put("status", parse_enum(body, "status", TASK_STATUSES, default="todo"), "status" in body)
    put("due_date", parse_date(body, "due_date"), "due_date" in body)
    put("estimated_minutes", parse_int(body, "estimated_minutes", min_value=1, max_value=24 * 60), "estimated_minutes" in body)
    put("scheduled_start", parse_datetime(body, "scheduled_start"), "scheduled_start" in body)
    put("scheduled_end", parse_datetime(body, "scheduled_end"), "scheduled_end" in body)
    put("calendar_uid", parse_str(body, "calendar_uid", max_len=255), "calendar_uid" in body)
    put("source", parse_enum(body, "source", TASK_SOURCES, default="manual"), "source" in body)
    put("source_ref", parse_str(body, "source_ref", max_len=255), "source_ref" in body)

    quadrant = parse_enum(body, "quadrant", tuple(QUADRANTS), default=None)
    if quadrant:
        out["urgent"], out["important"] = QUADRANTS[quadrant]
    return out
