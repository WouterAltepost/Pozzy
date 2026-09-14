from flask import Blueprint, g

from ...auth import require_auth
from ...errors import ok

bp = Blueprint("me", __name__, url_prefix="/api")


@bp.get("/me")
@require_auth
def me():
    return ok({"id": g.user["id"], "email": g.user["email"]})
