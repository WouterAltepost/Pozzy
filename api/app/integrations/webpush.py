"""Web Push sender (VAPID). The only place that talks to push services.

A subscription the push service reports as gone (404 or 410) is deleted, so a browser that
was reset or uninstalled stops costing a request on every run.
"""
import json
import logging

from flask import current_app

from ..extensions import db
from ..models import PushSubscription

log = logging.getLogger(__name__)


def configured() -> bool:
    return bool(current_app.config.get("VAPID_PUBLIC_KEY") and current_app.config.get("VAPID_PRIVATE_KEY"))


def send(sub: PushSubscription, payload: dict) -> bool:
    """Send one notification. Returns True when the push service accepted it."""
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
            data=json.dumps(payload),
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims={"sub": current_app.config.get("VAPID_SUBJECT") or "mailto:admin@example.com"},
            ttl=60 * 60 * 4,
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            log.info("push subscription gone (%s), removing", status)
            db.session.delete(sub)
            db.session.commit()
        else:
            log.warning("push failed: %s", exc)
        return False


def broadcast(payload: dict) -> dict:
    """Send to every subscription. Returns counts so callers can report honestly."""
    subs = db.session.query(PushSubscription).all()
    sent = sum(1 for s in subs if send(s, payload))
    return {"subscriptions": len(subs), "sent": sent}
