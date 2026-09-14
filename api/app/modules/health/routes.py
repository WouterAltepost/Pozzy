from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app
from sqlalchemy import text

from ...errors import ok
from ...extensions import db

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    """Unauthenticated liveness check. Reports DB reachability without failing."""
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        current_app.logger.exception("health: database check failed")
        db.session.rollback()
        db_ok = False
    now = datetime.now(ZoneInfo(current_app.config["TZ"]))
    from ...scheduler import scheduler_status

    return ok({"status": "ok", "db": db_ok, "time": now.isoformat(), "scheduler": scheduler_status()})
