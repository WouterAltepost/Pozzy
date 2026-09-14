from flask import Blueprint, request
from sqlalchemy import select

from ...auth import require_auth
from ...errors import fail, ok
from ...extensions import db
from ...models import JobRun, Setting
from ...settings_defaults import DEFAULTS, get_all_settings
from ...utils.dates import iso

bp = Blueprint("settings", __name__, url_prefix="/api")


@bp.get("/settings")
@require_auth
def get_settings():
    """Stored values merged over settings_defaults.DEFAULTS, so every known key is always present."""
    return ok(get_all_settings())


@bp.get("/settings/defaults")
@require_auth
def get_defaults():
    return ok(DEFAULTS)


@bp.put("/settings")
@require_auth
def put_settings():
    """Upsert the given keys. Keys not present in the body are left untouched."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not body:
        return fail("validation_error", "Body must be a non-empty JSON object of key/value pairs", 400)
    if any(not isinstance(key, str) or not key.strip() for key in body):
        return fail("validation_error", "Setting keys must be non-empty strings", 400)

    for key, value in body.items():
        row = db.session.scalar(select(Setting).where(Setting.key == key))
        if row is None:
            db.session.add(Setting(key=key, value=value))
        else:
            row.value = value
    db.session.commit()
    return ok(get_all_settings())


@bp.get("/settings/job-runs")
@require_auth
def job_runs():
    """Latest background job runs (plan section 7: failures must be visible in Settings)."""
    limit = max(1, min(request.args.get("limit", type=int) or 50, 500))
    rows = db.session.scalars(select(JobRun).order_by(JobRun.started_at.desc()).limit(limit)).all()
    return ok(
        [
            {"id": str(r.id), "name": r.name, "started_at": iso(r.started_at), "finished_at": iso(r.finished_at), "ok": r.ok, "message": r.message}
            for r in rows
        ]
    )
