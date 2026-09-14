from flask import Blueprint
from sqlalchemy import select

from ...auth import require_auth
from ...errors import ok
from ...extensions import db
from ...models import Area

bp = Blueprint("areas", __name__, url_prefix="/api")


@bp.get("/areas")
@require_auth
def list_areas():
    rows = db.session.scalars(select(Area).order_by(Area.sort_order, Area.name)).all()
    return ok([row.to_dict() for row in rows])
