from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.validation import parse_bool, parse_str, parse_tags, parse_uuid, register_validation_handler, require_object, to_uuid
from . import service

bp = Blueprint("notes", __name__, url_prefix="/api/notes")
register_validation_handler(bp)


def _fields(body: dict, partial: bool) -> dict:
    out = {}
    if "title" in body or not partial:
        out["title"] = parse_str(body, "title", required=True, max_len=200)
    if "body" in body or not partial:
        out["body"] = parse_str(body, "body", default="") or ""
    if "area_id" in body:
        out["area_id"] = parse_uuid(body, "area_id")
    if "tags" in body:
        out["tags"] = parse_tags(body, default=[])
    if "pinned" in body:
        out["pinned"] = parse_bool(body, "pinned", default=False)
    return out


@bp.get("")
@require_auth
def list_notes():
    args = request.args
    area_id = to_uuid(args["area_id"]) if args.get("area_id") else None
    return ok([n.to_dict() for n in service.list_notes(area_id, args.get("tag") or None, args.get("q") or None)])


@bp.post("")
@require_auth
def create_note():
    fields = _fields(require_object(request.get_json(silent=True)), partial=False)
    return ok(service.create_note(fields).to_dict(), 201)


@bp.get("/<note_id>")
@require_auth
def get_note(note_id):
    note = service.get_note(note_id)
    return ok(note.to_dict()) if note else fail("not_found", "Note not found", 404)


@bp.patch("/<note_id>")
@require_auth
def update_note(note_id):
    note = service.get_note(note_id)
    if note is None:
        return fail("not_found", "Note not found", 404)
    fields = _fields(require_object(request.get_json(silent=True)), partial=True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_note(note, fields).to_dict())


@bp.delete("/<note_id>")
@require_auth
def delete_note(note_id):
    note = service.get_note(note_id)
    if note is None:
        return fail("not_found", "Note not found", 404)
    service.delete_note(note)
    return ok({"deleted": note_id})
