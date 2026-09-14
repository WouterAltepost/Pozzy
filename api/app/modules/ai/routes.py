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


@bp.get("/briefing/context")
@require_auth
def briefing_context():
    """The facts the briefing is built from. Handy for checking why a briefing said something."""
    return ok(briefing.build_context(_day_arg()))
