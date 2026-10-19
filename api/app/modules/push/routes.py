"""Web Push subscriptions for habit reminders."""
from flask import Blueprint, current_app, request
from sqlalchemy import select

from ...auth import require_auth
from ...errors import fail, ok
from ...extensions import db
from ...integrations import webpush
from ...models import PushSubscription
from ...utils.validation import parse_str, register_validation_handler, require_object

bp = Blueprint("push", __name__, url_prefix="/api/push")
register_validation_handler(bp)


@bp.get("/config")
@require_auth
def config():
    """The VAPID public key the browser subscribes with, and how many devices are subscribed."""
    count = db.session.query(PushSubscription).count()
    return ok({"configured": webpush.configured(), "public_key": current_app.config.get("VAPID_PUBLIC_KEY"), "subscriptions": count})


@bp.post("/subscriptions")
@require_auth
def subscribe():
    body = require_object(request.get_json(silent=True))
    endpoint = parse_str(body, "endpoint", required=True, max_len=2000)
    keys = body.get("keys") if isinstance(body.get("keys"), dict) else {}
    p256dh = parse_str(keys, "p256dh", required=True, max_len=200)
    auth = parse_str(keys, "auth", required=True, max_len=100)
    sub = db.session.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    if sub is None:
        sub = PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.session.add(sub)
    else:
        sub.p256dh, sub.auth = p256dh, auth
    sub.user_agent = (request.headers.get("User-Agent") or "")[:300] or None
    db.session.commit()
    return ok(sub.to_dict(), 201)


@bp.delete("/subscriptions")
@require_auth
def unsubscribe():
    body = require_object(request.get_json(silent=True))
    endpoint = parse_str(body, "endpoint", required=True, max_len=2000)
    sub = db.session.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    if sub is not None:
        db.session.delete(sub)
        db.session.commit()
    return ok({"deleted": sub is not None})


@bp.post("/test")
@require_auth
def test():
    if not webpush.configured():
        return fail("not_configured", "Push is not configured on the server (VAPID keys missing)", 409)
    result = webpush.broadcast({"title": "Pozzy", "body": "Notifications work. Reminders arrive like this.", "url": "/", "tag": "pozzy-test"})
    return ok(result)
