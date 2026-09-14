from ...models.email import EMAIL_CATEGORIES, EMAIL_PRIORITIES
from ...utils.validation import ValidationError, parse_bool, parse_str, parse_uuid, require_object


def parse_email_patch(body) -> dict:
    """Fields the UI may change on an email: handled and the three overrides. Null clears an override."""
    body = require_object(body)
    out = {}
    if "handled" in body:
        out["handled"] = parse_bool(body, "handled", default=False)
    if "priority_override" in body:
        value = body["priority_override"]
        if value is not None and (isinstance(value, bool) or value not in EMAIL_PRIORITIES):
            raise ValidationError("'priority_override' must be 1, 2, 3, 4 or null")
        out["priority_override"] = value
    if "category_override" in body:
        value = body["category_override"]
        if value is not None and value not in EMAIL_CATEGORIES:
            raise ValidationError("'category_override' must be one of: " + ", ".join(EMAIL_CATEGORIES) + ", or null")
        out["category_override"] = value
    if "area_override_id" in body:
        out["area_override_id"] = parse_uuid(body, "area_override_id")
    if not out:
        raise ValidationError("No updatable fields in body")
    return out


def parse_account_patch(body) -> dict:
    body = require_object(body)
    out = {}
    if "label" in body:
        out["label"] = parse_str(body, "label", required=True, max_len=60)
    if "color" in body:
        out["color"] = parse_str(body, "color", max_len=20)
    if "enabled" in body:
        out["enabled"] = parse_bool(body, "enabled", default=True)
    if "sort_order" in body:
        value = body["sort_order"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError("'sort_order' must be an integer")
        out["sort_order"] = value
    if not out:
        raise ValidationError("No updatable fields in body")
    return out


def parse_task_overrides(body) -> dict:
    """Optional overrides for task-from-email. Delegates field rules to A's task schema."""
    if body is None:
        return {}
    from ..tasks.schemas import parse_task_body

    body = require_object(body)
    allowed = {k: v for k, v in body.items() if k in ("title", "description", "area_id", "urgent", "important", "due_date", "estimated_minutes", "tags", "quadrant")}
    if not allowed:
        return {}
    return parse_task_body(allowed, partial=True)
