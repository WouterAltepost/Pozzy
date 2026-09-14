from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.dates import today_local, week_start_of
from ...utils.validation import (
    date_from_str,
    parse_bool,
    parse_date,
    parse_number,
    parse_str,
    parse_uuid,
    register_validation_handler,
    require_object,
)
from . import service

bp = Blueprint("goals", __name__, url_prefix="/api/goals")
register_validation_handler(bp)


def _fields(body: dict, partial: bool) -> dict:
    out = {}
    if "title" in body or not partial:
        out["title"] = parse_str(body, "title", required=True, max_len=200)
    if "area_id" in body:
        out["area_id"] = parse_uuid(body, "area_id")
    if "target_value" in body:
        out["target_value"] = parse_number(body, "target_value")
    if "current_value" in body:
        out["current_value"] = parse_number(body, "current_value", default=0.0)
    if "done" in body:
        out["done"] = parse_bool(body, "done", default=False)
    if "notes" in body:
        out["notes"] = parse_str(body, "notes")
    if "week_start" in body:
        out["week_start"] = parse_date(body, "week_start")
    return out


@bp.get("")
@require_auth
def list_goals():
    raw = request.args.get("week_start")
    week = week_start_of(date_from_str(raw, "week_start")) if raw else week_start_of(today_local())
    return ok({"week_start": week.isoformat(), "goals": [g.to_dict() for g in service.list_goals(week)]})


@bp.post("")
@require_auth
def create_goal():
    fields = _fields(require_object(request.get_json(silent=True)), partial=False)
    return ok(service.create_goal(fields).to_dict(), 201)


@bp.patch("/<goal_id>")
@require_auth
def update_goal(goal_id):
    goal = service.get_goal(goal_id)
    if goal is None:
        return fail("not_found", "Goal not found", 404)
    fields = _fields(require_object(request.get_json(silent=True)), partial=True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_goal(goal, fields).to_dict())


@bp.post("/<goal_id>/progress")
@require_auth
def add_progress(goal_id):
    goal = service.get_goal(goal_id)
    if goal is None:
        return fail("not_found", "Goal not found", 404)
    body = require_object(request.get_json(silent=True) or {})
    delta = parse_number(body, "delta", default=1.0)
    return ok(service.add_progress(goal, delta).to_dict())


@bp.delete("/<goal_id>")
@require_auth
def delete_goal(goal_id):
    goal = service.get_goal(goal_id)
    if goal is None:
        return fail("not_found", "Goal not found", 404)
    service.delete_goal(goal)
    return ok({"deleted": goal_id})
