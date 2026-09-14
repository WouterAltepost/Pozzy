"""Request validation for the calendar routes. Plain functions, no framework."""
import re
from datetime import datetime, timedelta

from ...utils.dates import app_tz


class ValidationError(ValueError):
    pass


def parse_datetime(value, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field}' must be an ISO 8601 datetime string")
    # A raw "+02:00" in a query string arrives as " 02:00"; accept both.
    value = re.sub(r" (\d{2}:?\d{2})$", r"+\1", value.strip())
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"'{field}' is not a valid ISO 8601 datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=app_tz())
    return parsed


def parse_range(args) -> tuple[datetime, datetime]:
    """?start=&end= query params. Defaults to today plus 7 days in the app timezone."""
    if args.get("start"):
        start = parse_datetime(args.get("start"), "start")
    else:
        now = datetime.now(app_tz())
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = parse_datetime(args.get("end"), "end") if args.get("end") else start + timedelta(days=7)
    if end <= start:
        raise ValidationError("'end' must be after 'start'")
    if end - start > timedelta(days=92):
        raise ValidationError("range must be 92 days or less")
    return start, end


def _optional_text(body: dict, field: str, max_len: int) -> str | None:
    value = body.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")
    value = value.strip()
    if len(value) > max_len:
        raise ValidationError(f"'{field}' is longer than {max_len} characters")
    return value or None


def parse_event_body(body, *, partial: bool = False) -> dict:
    """Validate a create (all fields) or update (only given fields) payload."""
    if not isinstance(body, dict) or (not body and partial):
        raise ValidationError("Body must be a JSON object")
    out: dict = {}
    if "title" in body or not partial:
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("'title' is required")
        if len(title.strip()) > 500:
            raise ValidationError("'title' is longer than 500 characters")
        out["title"] = title.strip()
    if "start" in body or not partial:
        out["start"] = parse_datetime(body.get("start"), "start")
    if "end" in body or not partial:
        out["end"] = parse_datetime(body.get("end"), "end")
    if "all_day" in body:
        if not isinstance(body["all_day"], bool):
            raise ValidationError("'all_day' must be a boolean")
        out["all_day"] = body["all_day"]
    elif not partial:
        out["all_day"] = False
    for field, max_len in (("location", 500), ("description", 5000)):
        if field in body:
            out[field] = _optional_text(body, field, max_len)
        elif not partial:
            out[field] = None
    if "calendar_url" in body:
        url = body["calendar_url"]
        if url is not None and (not isinstance(url, str) or not url.strip()):
            raise ValidationError("'calendar_url' must be a non-empty string or null")
        out["calendar_url"] = url
    return out
