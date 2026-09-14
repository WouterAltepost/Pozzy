"""Request body parsing shared by stream A modules.

Schemas raise ValidationError; each blueprint registers `handle_validation_error`
so the error becomes a 400 in the standard envelope.
"""
import uuid
from datetime import date, datetime, timezone

from ..errors import fail


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def handle_validation_error(exc: ValidationError):
    return fail("validation_error", exc.message, 400)


def register_validation_handler(bp) -> None:
    bp.register_error_handler(ValidationError, handle_validation_error)


def require_object(body) -> dict:
    if not isinstance(body, dict):
        raise ValidationError("Body must be a JSON object")
    return body


def parse_str(body: dict, key: str, *, required=False, max_len=None, default=None):
    if key not in body:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    value = body[key]
    if value is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"'{key}' must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"'{key}' must not be empty")
    if max_len and len(value) > max_len:
        raise ValidationError(f"'{key}' must be at most {max_len} characters")
    return value


def parse_bool(body: dict, key: str, default=None):
    if key not in body or body[key] is None:
        return default
    if not isinstance(body[key], bool):
        raise ValidationError(f"'{key}' must be a boolean")
    return body[key]


def parse_int(body: dict, key: str, *, default=None, min_value=None, max_value=None, required=False):
    if key not in body or body[key] is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    value = body[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"'{key}' must be an integer")
    if min_value is not None and value < min_value:
        raise ValidationError(f"'{key}' must be at least {min_value}")
    if max_value is not None and value > max_value:
        raise ValidationError(f"'{key}' must be at most {max_value}")
    return value


def parse_number(body: dict, key: str, *, default=None, required=False):
    if key not in body or body[key] is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    value = body[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"'{key}' must be a number")
    return float(value)


def parse_enum(body: dict, key: str, allowed, *, default=None, required=False):
    value = parse_str(body, key, required=required, default=default)
    if value is None:
        return default
    if value not in allowed:
        raise ValidationError(f"'{key}' must be one of: {', '.join(allowed)}")
    return value


def parse_uuid(body: dict, key: str, *, default=None, required=False):
    if key not in body or body[key] is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    try:
        return uuid.UUID(str(body[key]))
    except (ValueError, TypeError):
        raise ValidationError(f"'{key}' must be a UUID")


def to_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def parse_date(body: dict, key: str, *, default=None, required=False) -> date | None:
    if key not in body or body[key] is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    return date_from_str(body[key], key)


def date_from_str(value, key="date") -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError(f"'{key}' must be a date (YYYY-MM-DD)")


def parse_datetime(body: dict, key: str, *, default=None, required=False) -> datetime | None:
    """Parse an ISO 8601 datetime. Naive values are treated as UTC. Result is UTC aware."""
    if key not in body or body[key] is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    return datetime_from_str(body[key], key)


def datetime_from_str(value, key="datetime") -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(f"'{key}' must be an ISO 8601 datetime")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_tags(body: dict, key: str = "tags", default=None):
    if key not in body or body[key] is None:
        return default
    value = body[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValidationError(f"'{key}' must be a list of strings")
    cleaned = []
    for item in value:
        item = item.strip()
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned
