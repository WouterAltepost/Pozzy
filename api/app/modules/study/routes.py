from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...models.application import APPLICATION_STATUSES
from ...models.course import COURSE_STATUSES
from ...models.deadline import DEADLINE_TYPES
from ...utils.validation import (
    parse_bool,
    parse_date,
    parse_datetime,
    parse_enum,
    parse_number,
    parse_str,
    parse_uuid,
    register_validation_handler,
    require_object,
    to_uuid,
)
from . import service

bp = Blueprint("study", __name__, url_prefix="/api/study")
register_validation_handler(bp)


def _course_fields(body, partial):
    out = {}
    if "name" in body or not partial:
        out["name"] = parse_str(body, "name", required=True, max_len=200)
    if "code" in body:
        out["code"] = parse_str(body, "code", max_len=50)
    if "period" in body:
        out["period"] = parse_str(body, "period", max_len=50)
    if "ects" in body:
        out["ects"] = parse_number(body, "ects")
    if "status" in body:
        out["status"] = parse_enum(body, "status", COURSE_STATUSES, default="active")
    return out


def _deadline_fields(body, partial):
    out = {}
    if "course_id" in body or not partial:
        out["course_id"] = parse_uuid(body, "course_id", required=True)
    if "title" in body or not partial:
        out["title"] = parse_str(body, "title", required=True, max_len=200)
    if "due_at" in body or not partial:
        out["due_at"] = parse_datetime(body, "due_at", required=True)
    if "type" in body:
        out["type"] = parse_enum(body, "type", DEADLINE_TYPES, default="assignment")
    if "done" in body:
        out["done"] = parse_bool(body, "done", default=False)
    return out


def _application_fields(body, partial):
    out = {}
    if "company" in body or not partial:
        out["company"] = parse_str(body, "company", required=True, max_len=200)
    if "role" in body:
        out["role"] = parse_str(body, "role", max_len=200)
    if "status" in body:
        out["status"] = parse_enum(body, "status", APPLICATION_STATUSES, default="found")
    if "applied_at" in body:
        out["applied_at"] = parse_date(body, "applied_at")
    if "next_step" in body:
        out["next_step"] = parse_str(body, "next_step", max_len=200)
    if "next_step_date" in body:
        out["next_step_date"] = parse_date(body, "next_step_date")
    if "notes" in body:
        out["notes"] = parse_str(body, "notes")
    if "link" in body:
        out["link"] = parse_str(body, "link", max_len=500)
    return out


# Courses


@bp.get("/courses")
@require_auth
def list_courses():
    include = request.args.get("include_closed") in ("1", "true")
    return ok([c.to_dict(with_deadlines=True) for c in service.list_courses(include)])


@bp.post("/courses")
@require_auth
def create_course():
    return ok(service.create_course(_course_fields(require_object(request.get_json(silent=True)), False)).to_dict(), 201)


@bp.patch("/courses/<course_id>")
@require_auth
def update_course(course_id):
    course = service.get_course(course_id)
    if course is None:
        return fail("not_found", "Course not found", 404)
    fields = _course_fields(require_object(request.get_json(silent=True)), True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_course(course, fields).to_dict())


@bp.delete("/courses/<course_id>")
@require_auth
def delete_course(course_id):
    course = service.get_course(course_id)
    if course is None:
        return fail("not_found", "Course not found", 404)
    service.delete_course(course)
    return ok({"deleted": course_id})


# Deadlines


@bp.get("/deadlines")
@require_auth
def list_deadlines():
    include = request.args.get("include_done") in ("1", "true")
    course_id = to_uuid(request.args["course_id"]) if request.args.get("course_id") else None
    return ok([d.to_dict() for d in service.list_deadlines(include, course_id)])


@bp.post("/deadlines")
@require_auth
def create_deadline():
    return ok(service.create_deadline(_deadline_fields(require_object(request.get_json(silent=True)), False)).to_dict(), 201)


@bp.patch("/deadlines/<deadline_id>")
@require_auth
def update_deadline(deadline_id):
    deadline = service.get_deadline(deadline_id)
    if deadline is None:
        return fail("not_found", "Deadline not found", 404)
    fields = _deadline_fields(require_object(request.get_json(silent=True)), True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_deadline(deadline, fields).to_dict())


@bp.delete("/deadlines/<deadline_id>")
@require_auth
def delete_deadline(deadline_id):
    deadline = service.get_deadline(deadline_id)
    if deadline is None:
        return fail("not_found", "Deadline not found", 404)
    service.delete_deadline(deadline)
    return ok({"deleted": deadline_id})


# Applications


@bp.get("/applications")
@require_auth
def list_applications():
    return ok([a.to_dict() for a in service.list_applications()])


@bp.post("/applications")
@require_auth
def create_application():
    return ok(service.create_application(_application_fields(require_object(request.get_json(silent=True)), False)).to_dict(), 201)


@bp.patch("/applications/<app_id>")
@require_auth
def update_application(app_id):
    row = service.get_application(app_id)
    if row is None:
        return fail("not_found", "Application not found", 404)
    fields = _application_fields(require_object(request.get_json(silent=True)), True)
    if not fields:
        return fail("validation_error", "No updatable fields in body", 400)
    return ok(service.update_application(row, fields).to_dict())


@bp.delete("/applications/<app_id>")
@require_auth
def delete_application(app_id):
    row = service.get_application(app_id)
    if row is None:
        return fail("not_found", "Application not found", 404)
    service.delete_application(row)
    return ok({"deleted": app_id})


@bp.get("/upcoming")
@require_auth
def upcoming():
    days = request.args.get("days", type=int) or 14
    return ok(service.upcoming(max(1, min(days, 90))))
