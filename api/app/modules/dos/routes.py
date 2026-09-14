from datetime import timedelta

from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.dates import today_local
from ...utils.validation import (
    ValidationError,
    date_from_str,
    parse_bool,
    parse_date,
    parse_int,
    parse_str,
    parse_uuid,
    register_validation_handler,
    require_object,
)
from . import service

bp = Blueprint("dos", __name__, url_prefix="/api/dos")
register_validation_handler(bp)


def _range_from_args():
    args = request.args
    if args.get("date"):
        day = date_from_str(args["date"])
        return day, day
    start = date_from_str(args["from"], "from") if args.get("from") else today_local()
    end = date_from_str(args["to"], "to") if args.get("to") else start + timedelta(days=1)
    if end < start:
        raise ValidationError("'to' must not be before 'from'")
    if (end - start).days > 62:
        raise ValidationError("Range too large (max 62 days)")
    return start, end


@bp.get("")
@require_auth
def list_dos():
    start, end = _range_from_args()
    return ok([d.to_dict() for d in service.list_dos(start, end)])


@bp.post("")
@require_auth
def create_do():
    body = require_object(request.get_json(silent=True))
    fields = {
        "date": parse_date(body, "date"),
        "title": parse_str(body, "title", max_len=200),
        "task_id": parse_uuid(body, "task_id"),
        "position": parse_int(body, "position", min_value=1, max_value=20),
        "done": parse_bool(body, "done", default=False),
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    return ok(service.create_do(fields).to_dict(), 201)


@bp.patch("/<do_id>")
@require_auth
def update_do(do_id):
    do = service.get_do(do_id)
    if do is None:
        return fail("not_found", "Do not found", 404)
    body = require_object(request.get_json(silent=True))
    fields = {}
    if "title" in body:
        fields["title"] = parse_str(body, "title", required=True, max_len=200)
    if "done" in body:
        fields["done"] = parse_bool(body, "done", default=False)
    if "position" in body:
        fields["position"] = parse_int(body, "position", min_value=1, max_value=20, required=True)
    if "date" in body:
        fields["date"] = parse_date(body, "date", required=True)
    if "task_id" in body:
        fields["task_id"] = parse_uuid(body, "task_id")
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_do(do, fields).to_dict())


@bp.delete("/<do_id>")
@require_auth
def delete_do(do_id):
    do = service.get_do(do_id)
    if do is None:
        return fail("not_found", "Do not found", 404)
    service.delete_do(do)
    return ok({"deleted": do_id})


@bp.post("/suggest")
@require_auth
def suggest():
    body = require_object(request.get_json(silent=True) or {})
    day = parse_date(body, "date") or today_local()
    return ok(service.suggest_dos(day))


@bp.post("/rollover")
@require_auth
def rollover_now():
    """Manual trigger of the rollover job for today (idempotent)."""
    from flask import current_app

    from ...jobs import three_do_rollover

    message = three_do_rollover.run(current_app._get_current_object())
    return ok({"message": message})
