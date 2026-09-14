from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.validation import parse_enum, parse_str, register_validation_handler, require_object
from . import service

bp = Blueprint("captures", __name__, url_prefix="/api/captures")
register_validation_handler(bp)


def _load(capture_id):
    row = service.get_capture(capture_id)
    return row if row else None


@bp.get("")
@require_auth
def list_captures():
    status = request.args.get("status") or None
    if status and status not in ("new", "processed", "discarded"):
        return fail("validation_error", "status must be new, processed or discarded", 400)
    return ok([c.to_dict() for c in service.list_captures(status)])


@bp.post("")
@require_auth
def create_capture():
    body = require_object(request.get_json(silent=True))
    text = parse_str(body, "text", required=True, max_len=4000)
    if not text.strip():
        return fail("validation_error", "'text' is empty", 400)
    row = service.create_capture(text)
    if body.get("process") is True:
        row = service.process_capture(row)
    return ok(row.to_dict(), 201)


@bp.get("/<capture_id>")
@require_auth
def get_capture(capture_id):
    row = _load(capture_id)
    return ok(row.to_dict()) if row else fail("not_found", "Capture not found", 404)


@bp.post("/<capture_id>/process")
@require_auth
def process_capture(capture_id):
    row = _load(capture_id)
    if row is None:
        return fail("not_found", "Capture not found", 404)
    return ok(service.process_capture(row).to_dict())


@bp.post("/<capture_id>/confirm")
@require_auth
def confirm_capture(capture_id):
    row = _load(capture_id)
    if row is None:
        return fail("not_found", "Capture not found", 404)
    body = require_object(request.get_json(silent=True) or {})
    kind = parse_enum(body, "type", ("task", "event", "goal", "note", "tracker")) if "type" in body else None
    fields = body.get("fields")
    if fields is not None and not isinstance(fields, dict):
        return fail("validation_error", "'fields' must be an object", 400)
    row, created = service.confirm_capture(row, kind, fields)
    return ok({"capture": row.to_dict(), "created": created})


@bp.post("/<capture_id>/discard")
@require_auth
def discard_capture(capture_id):
    row = _load(capture_id)
    if row is None:
        return fail("not_found", "Capture not found", 404)
    return ok(service.discard_capture(row).to_dict())


@bp.delete("/<capture_id>")
@require_auth
def delete_capture(capture_id):
    row = _load(capture_id)
    if row is None:
        return fail("not_found", "Capture not found", 404)
    service.delete_capture(row)
    return ok({"deleted": capture_id})
