from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...utils.validation import parse_int, register_validation_handler, require_object, to_uuid
from . import service
from .schemas import QUADRANTS, parse_task_body

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")
register_validation_handler(bp)


def _not_found():
    return fail("not_found", "Task not found", 404)


@bp.get("")
@require_auth
def list_tasks():
    args = request.args
    status = [s for s in args.get("status", "").split(",") if s] or None
    quadrant = args.get("quadrant") or None
    if quadrant and quadrant not in QUADRANTS:
        return fail("validation_error", "Unknown quadrant", 400)
    area_id = to_uuid(args.get("area_id")) if args.get("area_id") else None
    rows = service.list_tasks(
        status=status,
        area_id=area_id,
        quadrant=quadrant,
        due=args.get("due") or None,
        q=args.get("q") or None,
        include_closed=args.get("include_closed") in ("1", "true"),
    )
    return ok([t.to_dict() for t in rows])


@bp.post("")
@require_auth
def create_task():
    fields = parse_task_body(request.get_json(silent=True), partial=False)
    task = service.create_task(fields)
    return ok(task.to_dict(), 201)


@bp.get("/<task_id>")
@require_auth
def get_task(task_id):
    task = service.get_task(task_id)
    return ok(task.to_dict()) if task else _not_found()


@bp.patch("/<task_id>")
@bp.put("/<task_id>")
@require_auth
def update_task(task_id):
    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    fields = parse_task_body(request.get_json(silent=True), partial=True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_task(task, fields).to_dict())


@bp.delete("/<task_id>")
@require_auth
def delete_task(task_id):
    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    service.delete_task(task)
    return ok({"deleted": task_id})


@bp.post("/<task_id>/complete")
@require_auth
def complete_task(task_id):
    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    body = require_object(request.get_json(silent=True) or {})
    minutes = parse_int(body, "actual_minutes", min_value=1, max_value=24 * 60)
    return ok(service.complete_task(task, minutes).to_dict())


@bp.post("/<task_id>/move")
@require_auth
def move_task(task_id):
    """Eisenhower board drag target: {"quadrant": "do"|"schedule"|"delegate"|"eliminate"}."""
    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    body = require_object(request.get_json(silent=True))
    quadrant = body.get("quadrant")
    if quadrant not in QUADRANTS:
        return fail("validation_error", "'quadrant' must be one of: " + ", ".join(QUADRANTS), 400)
    urgent, important = QUADRANTS[quadrant]
    return ok(service.update_task(task, {"urgent": urgent, "important": important}).to_dict())


@bp.post("/<task_id>/suggest-slot")
@require_auth
def suggest_slot(task_id):
    from ...utils.validation import parse_datetime
    from . import scheduling

    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    body = require_object(request.get_json(silent=True) or {})
    duration = parse_int(body, "duration_minutes", min_value=5, max_value=24 * 60)
    from_dt = parse_datetime(body, "from")
    return ok(scheduling.suggest_slots(task, duration_min=duration, from_dt=from_dt))


@bp.post("/<task_id>/schedule")
@require_auth
def schedule(task_id):
    from ...utils.validation import parse_datetime
    from . import scheduling

    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    body = require_object(request.get_json(silent=True))
    start = parse_datetime(body, "start", required=True)
    end = parse_datetime(body, "end")
    return ok(scheduling.schedule_task(task, start, end).to_dict())


@bp.post("/<task_id>/unschedule")
@require_auth
def unschedule(task_id):
    from . import scheduling

    task = service.get_task(task_id)
    if task is None:
        return _not_found()
    return ok(scheduling.unschedule_task(task).to_dict())
