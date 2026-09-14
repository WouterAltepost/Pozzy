from flask import Blueprint, request
from sqlalchemy import select

from ...auth import require_auth
from ...errors import fail, ok
from ...extensions import db
from ...models import Setting

bp = Blueprint("settings", __name__, url_prefix="/api")


def _all_settings() -> dict:
    rows = db.session.scalars(select(Setting).order_by(Setting.key)).all()
    return {row.key: row.value for row in rows}


@bp.get("/settings")
@require_auth
def get_settings():
    return ok(_all_settings())


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
    return ok(_all_settings())
