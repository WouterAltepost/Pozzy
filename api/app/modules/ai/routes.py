from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.dates import today_local
from ...utils.validation import date_from_str, register_validation_handler
from . import briefing

bp = Blueprint("ai", __name__, url_prefix="/api/ai")
register_validation_handler(bp)


def _day_arg():
    raw = request.args.get("date") or (request.get_json(silent=True) or {}).get("date")
    return date_from_str(raw, "date") if raw else today_local()


@bp.get("/briefing")
@require_auth
def get_briefing():
    row = briefing.get_briefing(_day_arg())
    return ok(row.to_dict() if row else None)


@bp.post("/briefing")
@require_auth
def regenerate_briefing():
    """Generate (or regenerate) the briefing for a day. Works with AI off (deterministic text)."""
    return ok(briefing.generate_briefing(_day_arg(), force=True).to_dict())


@bp.post("/briefing/notes")
@require_auth
def add_briefing_note():
    """Reply to today's briefing. Claude rewrites the briefing and proposes actions; nothing is applied yet."""
    from ...utils.validation import parse_str, require_object

    body = require_object(request.get_json(silent=True))
    text = parse_str(body, "text", required=True, max_len=2000)
    return ok(briefing.add_note(_day_arg(), text).to_dict())


@bp.post("/briefing/notes/<int:note_index>/apply")
@require_auth
def apply_briefing_actions(note_index):
    """Apply the ticked actions of one note through the owning services."""
    from ...utils.validation import require_object

    body = require_object(request.get_json(silent=True))
    indexes = body.get("actions")
    if not isinstance(indexes, list) or any(not isinstance(i, int) for i in indexes):
        return fail("validation_error", "'actions' must be a list of action indexes", 400)
    row, results = briefing.apply_actions(_day_arg(), note_index, indexes)
    return ok({"briefing": row.to_dict(), "results": results})


@bp.get("/briefing/context")
@require_auth
def briefing_context():
    """The facts the briefing is built from. Handy for checking why a briefing said something."""
    return ok(briefing.build_context(_day_arg()))


@bp.post("/plan")
@require_auth
def plan():
    """Suggest placements for open tasks, deadline prep and goal work. Nothing is written;
    the client accepts each suggestion through the task schedule or event create endpoints."""
    from ...utils.validation import parse_int, require_object
    from . import planner

    body = require_object(request.get_json(silent=True) or {})
    start = date_from_str(body["start"], "start") if body.get("start") else today_local()
    days = parse_int(body, "days", default=7, min_value=1, max_value=14)
    return ok(planner.build_plan(start, days))


@bp.get("/spend")
@require_auth
def spend():
    from . import spend as spend_service

    return ok(spend_service.summary())
