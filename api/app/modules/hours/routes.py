from datetime import timedelta

from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...models import HoursLog
from ...extensions import db
from ...utils.dates import today_local, week_start_of
from ...utils.validation import (
    ValidationError,
    date_from_str,
    parse_date,
    parse_int,
    parse_str,
    parse_tags,
    parse_uuid,
    register_validation_handler,
    require_object,
    to_uuid,
)
from . import service

bp = Blueprint("hours", __name__, url_prefix="/api/hours")
register_validation_handler(bp)


def _fields(body: dict, partial: bool) -> dict:
    out = {}
    if "date" in body or not partial:
        out["date"] = parse_date(body, "date") or today_local()
    if "minutes" in body or not partial:
        out["minutes"] = parse_int(body, "minutes", required=True, min_value=1, max_value=24 * 60)
    if "area_id" in body:
        out["area_id"] = parse_uuid(body, "area_id")
    if "tags" in body:
        out["tags"] = parse_tags(body, default=[])
    if "note" in body:
        out["note"] = parse_str(body, "note")
    if "task_id" in body:
        out["task_id"] = parse_uuid(body, "task_id")
    return out


@bp.get("")
@require_auth
def list_logs():
    args = request.args
    start = date_from_str(args["from"], "from") if args.get("from") else week_start_of(today_local())
    end = date_from_str(args["to"], "to") if args.get("to") else start + timedelta(days=6)
    if end < start:
        raise ValidationError("'to' must not be before 'from'")
    return ok([log.to_dict() for log in service.list_logs(start, end)])


@bp.get("/week")
@require_auth
def week():
    raw = request.args.get("week_start")
    start = week_start_of(date_from_str(raw, "week_start")) if raw else None
    return ok(service.week_summary(start))


@bp.get("/suggestions")
@require_auth
def suggestions():
    """Past agenda events and completed tasks with no hours logged yet, to confirm or skip."""
    return ok(service.suggestions())


@bp.post("/suggestions/accept")
@require_auth
def accept_suggestions():
    body = require_object(request.get_json(silent=True))
    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError("'items' must be a non-empty list")
    picks = []
    for raw in items:
        item = require_object(raw)
        ref = parse_str(item, "ref", required=True, max_len=400)
        if not (ref.startswith("event:") or ref.startswith("task:")):
            raise ValidationError("'ref' must start with 'event:' or 'task:'")
        picks.append(
            {
                "ref": ref,
                "date": parse_date(item, "date") or today_local(),
                "minutes": parse_int(item, "minutes", required=True, min_value=1, max_value=24 * 60),
                "area_id": parse_uuid(item, "area_id"),
                "tags": parse_tags(item, default=[]),
                "note": parse_str(item, "note"),
            }
        )
    created = service.accept_suggestions(picks)
    return ok({"created": [log.to_dict() for log in created]}, 201)


@bp.post("/suggestions/dismiss")
@require_auth
def dismiss_suggestions():
    body = require_object(request.get_json(silent=True))
    refs = body.get("refs")
    if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r.strip() for r in refs):
        raise ValidationError("'refs' must be a non-empty list of strings")
    return ok({"dismissed": service.dismiss_suggestions([r.strip() for r in refs])})


@bp.post("")
@require_auth
def create_log():
    fields = _fields(require_object(request.get_json(silent=True)), partial=False)
    return ok(service.create_log(fields).to_dict(), 201)


@bp.patch("/<log_id>")
@require_auth
def update_log(log_id):
    key = to_uuid(log_id)
    log = db.session.get(HoursLog, key) if key else None
    if log is None:
        return fail("not_found", "Log not found", 404)
    fields = _fields(require_object(request.get_json(silent=True)), partial=True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_log(log, fields).to_dict())


@bp.delete("/<log_id>")
@require_auth
def delete_log(log_id):
    key = to_uuid(log_id)
    log = db.session.get(HoursLog, key) if key else None
    if log is None:
        return fail("not_found", "Log not found", 404)
    service.delete_log(log)
    return ok({"deleted": log_id})
