from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.dates import today_local, week_start_of
from ...utils.validation import date_from_str, register_validation_handler, require_object
from . import service

bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")
register_validation_handler(bp)


def _week(raw: str):
    if raw in ("current", "this"):
        return week_start_of(today_local())
    return week_start_of(date_from_str(raw, "week"))


@bp.get("")
@require_auth
def list_reviews():
    return ok([r.to_dict() for r in service.list_reviews()])


@bp.get("/<week>")
@require_auth
def get_review(week):
    row = service.get_review(_week(week))
    return ok(row.to_dict() if row else None)


@bp.post("/<week>/generate")
@require_auth
def generate(week):
    """Compute stats and draft the reflection and next week's focus. Overwrites an unfinalized draft."""
    return ok(service.generate_review(_week(week), force=True).to_dict())


@bp.post("/<week>/refresh-stats")
@require_auth
def refresh_stats(week):
    row = service.get_review(_week(week))
    if row is None:
        return fail("not_found", "No review for that week yet", 404)
    return ok(service.refresh_stats(row).to_dict())


@bp.patch("/<week>")
@require_auth
def update(week):
    row = service.get_review(_week(week))
    if row is None:
        return fail("not_found", "No review for that week yet", 404)
    body = require_object(request.get_json(silent=True))
    fields = {k: body[k] for k in ("notes", "reflection", "next_week_focus") if k in body}
    if not fields:
        return fail("validation_error", "Nothing to update", 400)
    return ok(service.update_review(row, fields).to_dict())


@bp.post("/<week>/finalize")
@require_auth
def finalize(week):
    row = service.get_review(_week(week))
    if row is None:
        return fail("not_found", "No review for that week yet", 404)
    row, created = service.finalize_review(row)
    return ok({"review": row.to_dict(), "created_goals": created})
