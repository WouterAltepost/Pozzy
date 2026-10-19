from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
import re

from ...models.tracker import SCHEDULES, TARGET_PERIODS, TRACKER_TYPES
from ...models.tracker_entry import ENTRY_STATUSES
from ...utils.dates import today_local, week_start_of
from ...utils.validation import (
    date_from_str,
    parse_bool,
    parse_date,
    parse_enum,
    parse_int,
    parse_number,
    parse_str,
    parse_uuid,
    ValidationError,
    register_validation_handler,
    require_object,
)
from . import service

bp = Blueprint("trackers", __name__, url_prefix="/api/trackers")
register_validation_handler(bp)


def _fields(body: dict, partial: bool) -> dict:
    out = {}
    if "name" in body or not partial:
        out["name"] = parse_str(body, "name", required=True, max_len=100)
    if "type" in body or not partial:
        out["type"] = parse_enum(body, "type", TRACKER_TYPES, required=True)
    if "area_id" in body:
        out["area_id"] = parse_uuid(body, "area_id")
    if "target_value" in body:
        out["target_value"] = parse_number(body, "target_value")
    if "target_period" in body:
        out["target_period"] = parse_enum(body, "target_period", TARGET_PERIODS, default="day")
    if "unit" in body:
        out["unit"] = parse_str(body, "unit", max_len=20)
    if "active" in body:
        out["active"] = parse_bool(body, "active", default=True)
    if "sort_order" in body:
        out["sort_order"] = parse_int(body, "sort_order", min_value=0)
    if "schedule" in body:
        out["schedule"] = parse_enum(body, "schedule", SCHEDULES, default="daily")
    if "schedule_days" in body:
        out["schedule_days"] = parse_int(body, "schedule_days", min_value=0, max_value=127)
    if "schedule_n" in body:
        out["schedule_n"] = parse_int(body, "schedule_n", min_value=2, max_value=60)
    if "icon" in body:
        out["icon"] = parse_str(body, "icon", max_len=40)
    if "reminder_time" in body:
        value = parse_str(body, "reminder_time", max_len=5)
        if value and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value):
            raise ValidationError("'reminder_time' must be HH:MM")
        out["reminder_time"] = value or None
    return out


def _entry_payload(tracker, entry, day) -> dict:
    """Entry endpoints answer with the entry (None once deleted) and the tracker's refreshed
    grid row for the week of `day`, so the client patches one row instead of reloading."""
    payload = entry.to_dict() if entry is not None else {"tracker_id": str(tracker.id), "date": day.isoformat(), "value": None, "note": None}
    payload["row"] = service.week_row(tracker, week_start_of(day))
    return payload


def _load(tracker_id):
    tracker = service.get_tracker(tracker_id)
    return tracker, (None if tracker else fail("not_found", "Tracker not found", 404))


@bp.get("")
@require_auth
def list_trackers():
    include = request.args.get("include_inactive") in ("1", "true")
    return ok([t.to_dict() for t in service.list_trackers(include)])


@bp.post("")
@require_auth
def create_tracker():
    fields = _fields(require_object(request.get_json(silent=True)), partial=False)
    return ok(service.create_tracker(fields).to_dict(), 201)


@bp.get("/week")
@require_auth
def week():
    raw = request.args.get("week_start")
    start = week_start_of(date_from_str(raw, "week_start")) if raw else None
    include = request.args.get("include_inactive") in ("1", "true")
    return ok(service.week_grid(start, include))


@bp.get("/series")
@require_auth
def series():
    """Every tracker over one range, for the live chart on the Tracking page."""
    include_inactive = request.args.get("include_inactive") in ("1", "true")
    if request.args.get("weeks") == "all":
        return ok(service.series(None, include_inactive))
    weeks = request.args.get("weeks", type=int) or 12
    return ok(service.series(max(1, min(weeks, 104)), include_inactive))


@bp.post("/reorder")
@require_auth
def reorder():
    body = require_object(request.get_json(silent=True))
    ids = body.get("ids")
    if not isinstance(ids, list) or not ids:
        return fail("validation_error", "'ids' must be a non-empty list", 400)
    return ok([t.to_dict() for t in service.reorder(ids)])


@bp.patch("/<tracker_id>")
@require_auth
def update_tracker(tracker_id):
    tracker, err = _load(tracker_id)
    if err:
        return err
    fields = _fields(require_object(request.get_json(silent=True)), partial=True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_tracker(tracker, fields).to_dict())


@bp.delete("/<tracker_id>")
@require_auth
def delete_tracker(tracker_id):
    tracker, err = _load(tracker_id)
    if err:
        return err
    service.delete_tracker(tracker)
    return ok({"deleted": tracker_id})


@bp.get("/<tracker_id>/history")
@require_auth
def history(tracker_id):
    tracker, err = _load(tracker_id)
    if err:
        return err
    if request.args.get("all") in ("1", "true"):
        return ok(service.history(tracker, None))
    weeks = request.args.get("weeks", type=int) or 8
    return ok(service.history(tracker, max(1, min(weeks, 52))))


@bp.get("/<tracker_id>/stats")
@require_auth
def stats(tracker_id):
    """Streaks, rates, heatmap, months, weekdays and notes for the habit detail page."""
    tracker, err = _load(tracker_id)
    if err:
        return err
    return ok(service.stats(tracker))


@bp.put("/<tracker_id>/entries")
@require_auth
def upsert_entry(tracker_id):
    tracker, err = _load(tracker_id)
    if err:
        return err
    body = require_object(request.get_json(silent=True))
    day = parse_date(body, "date") or today_local()
    status = parse_enum(body, "status", ENTRY_STATUSES, default="done")
    value = parse_number(body, "value", required=status != "skipped") or 0
    note = parse_str(body, "note")
    if value < 0:
        return fail("validation_error", "'value' must not be negative", 400)
    entry = service.upsert_entry(tracker, day, value, note, status)
    return ok(_entry_payload(tracker, entry, day))


@bp.delete("/<tracker_id>/entries/<day>")
@require_auth
def delete_entry(tracker_id, day):
    tracker, err = _load(tracker_id)
    if err:
        return err
    parsed = date_from_str(day)
    if not service.delete_entry(tracker, parsed):
        return fail("not_found", "Entry not found", 404)
    return ok({"deleted": day, "row": service.week_row(tracker, week_start_of(parsed))})


@bp.post("/<tracker_id>/tick")
@require_auth
def tick(tracker_id):
    tracker, err = _load(tracker_id)
    if err:
        return err
    body = require_object(request.get_json(silent=True) or {})
    day = parse_date(body, "date") or today_local()
    return ok(_entry_payload(tracker, service.tick(tracker, day), day))


@bp.post("/<tracker_id>/untick")
@require_auth
def untick(tracker_id):
    """Reverse one tap: toggle a bool back, subtract one step from a count or value."""
    tracker, err = _load(tracker_id)
    if err:
        return err
    body = require_object(request.get_json(silent=True) or {})
    day = parse_date(body, "date") or today_local()
    return ok(_entry_payload(tracker, service.untick(tracker, day), day))
