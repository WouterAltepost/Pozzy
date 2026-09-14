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
