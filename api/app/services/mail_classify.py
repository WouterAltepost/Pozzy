"""Email classification pipeline (stream C).

`classify_pending` picks unclassified emails in batches, asks D's
`claude_client.classify_emails(batch)` (contract in docs/AI_CONTRACTS.md,
Stream C) and falls back to `classify_rules` for every email the AI did not
answer for: kill switch off, function missing, exception, None, or an item
that fails validation. Only the raw classification columns are written; the
`*_override` columns are never touched, so re-classification cannot clobber a
manual override.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime

from sqlalchemy import select

from ..extensions import db
from ..integrations import claude_client
from ..models import Area, Email
from ..models.email import DEFAULT_CATEGORY, DEFAULT_PRIORITY, EMAIL_CATEGORIES, EMAIL_PRIORITIES
from ..settings_defaults import get_setting
from ..utils.dates import iso, now_utc

log = logging.getLogger(__name__)

AREA_NAMES = ("Study", "Work", "Personal", "Health")
SNIPPET_CHARS_FOR_AI = 1200

# Rule tables. Lower-case substring matches on sender address, sender name or subject.
NOTIFICATION_SENDERS = (
    "noreply", "no-reply", "no_reply", "donotreply", "do-not-reply", "notification", "notifications",
    "mailer-daemon", "postmaster", "alert", "alerts", "automated", "bounce", "system@", "support@",
    "security", "calendar-notification", "drive-shares", "team@", "hello@", "info@",
)
NOTIFICATION_SUBJECTS = (
    "security alert", "verification code", "verify your", "password reset", "sign-in", "new login",
    "delivery status", "build failed", "deploy", "your order", "shipped", "receipt for your", "confirm your",
    "2-step verification", "welcome to", "terms of service", "privacy policy", "privacybeleid",
)
NEWSLETTER_SENDERS = (
    "newsletter", "news@", "digest", "tldr", "substack", "medium.com", "mailchimp", "beehiiv", "list-",
    "updates@", "marketing", "promo", "hi@", "weekly", "campaign", "linkedin.com", "chess.com", "producthunt",
)
NEWSLETTER_SUBJECTS = (
    "newsletter", "digest", "this week", "weekly", "what you've missed", "unsubscribe", "top stories", "edition",
    "% off", "% korting", "korting", "voordeel", "aanbieding", "sale", "deal", "offer", "new arrivals", "just dropped", "last chance",
)
FINANCE_SENDERS = (
    "bank", "ing.nl", "ing.com", "rabobank", "abnamro", "bunq", "revolut", "degiro", "trading212", "paypal", "tikkie",
    "belastingdienst", "duo.nl", "invoice", "billing", "payments", "mollie", "stripe", "wise.com", "coinbase", "ibkr", "interactivebrokers",
)
FINANCE_SUBJECTS = ("invoice", "factuur", "payment", "betaling", "receipt", "statement", "afschrift", "declaratie", "salaris", "salary", "tax", "belasting", "refund")
SCHOOL_SENDERS = (".edu", "uni.", "uni-", "hva.nl", "uva.nl", "vu.nl", "tudelft", "student", "university", "universiteit", "hogeschool", "canvas", "brightspace", "blackboard", "osiris", "studielink", "surf.nl")
SCHOOL_SUBJECTS = ("exam", "tentamen", "prüfung", "vorlesung", "college", "lecture", "assignment", "opdracht", "course", "vak", "grade", "cijfer", "thesis", "scriptie", "deadline", "rooster", "schedule")
CLIENT_HINTS = ("alpaca", "udefine", "proposal", "offerte", "contract", "project", "client", "klant", "meeting", "afspraak", "quote")
PERSONAL_DOMAINS = ("gmail.com", "hotmail.com", "outlook.com", "live.nl", "live.com", "icloud.com", "me.com", "yahoo.com", "protonmail.com", "proton.me", "ziggo.nl", "kpnmail.nl")


def _has(haystack: str, needles) -> bool:
    return any(n in haystack for n in needles)


def classify_rules_one(item: dict) -> dict:
    """Deterministic classification for one batch item. Priority 3 except newsletters and
    notifications, which are low noise (4). needs_reply is always false."""
    sender = f"{item.get('from_email') or ''} {item.get('from_name') or ''}".lower()
    subject = (item.get("subject") or "").lower()
    domain = (item.get("from_email") or "").rsplit("@", 1)[-1].lower()
    account = (item.get("account_label") or "").lower()

    if _has(sender, NOTIFICATION_SENDERS) or _has(subject, NOTIFICATION_SUBJECTS):
        category, area, priority = "notification", None, 4
    elif _has(sender, NEWSLETTER_SENDERS) or _has(subject, NEWSLETTER_SUBJECTS):
        category, area, priority = "newsletter", None, 4
    elif _has(sender, FINANCE_SENDERS) or _has(subject, FINANCE_SUBJECTS):
        category, area, priority = "finance", "Personal", DEFAULT_PRIORITY
    elif _has(sender, SCHOOL_SENDERS) or _has(subject, SCHOOL_SUBJECTS):
        category, area, priority = "school", "Study", DEFAULT_PRIORITY
    elif account == "work" or _has(sender, CLIENT_HINTS) or _has(subject, CLIENT_HINTS):
        category, area, priority = "client", "Work", DEFAULT_PRIORITY
    elif domain in PERSONAL_DOMAINS:
        category, area, priority = "personal", "Personal", DEFAULT_PRIORITY
    else:
        category, area, priority = DEFAULT_CATEGORY, None, DEFAULT_PRIORITY

    return {
        "id": item["id"],
        "priority": priority,
        "category": category,
        "area": area,
        "needs_reply": False,
        "one_line_summary": (item.get("subject") or "(no subject)")[:200],
    }


def classify_rules(batch: list[dict]) -> list[dict]:
    return [classify_rules_one(item) for item in batch]


def build_batch(emails: list[Email]) -> list[dict]:
    """Input shape for claude_client.classify_emails (docs/AI_CONTRACTS.md, Stream C)."""
    return [
        {
            "id": str(e.id),
            "account_label": e.account.label if e.account else "",
            "from_name": e.from_name or "",
            "from_email": e.from_email or "",
            "subject": e.subject or "",
            "date": iso(e.date),
            "snippet": (e.snippet or "")[:SNIPPET_CHARS_FOR_AI],
        }
        for e in emails
    ]


def validate_item(item, allowed_ids: set[str]) -> dict | None:
    """Return a cleaned output item or None when it does not match the contract."""
    if not isinstance(item, dict):
        return None
    email_id = str(item.get("id") or "")
    if email_id not in allowed_ids:
        return None
    priority = item.get("priority")
    if isinstance(priority, bool) or not isinstance(priority, int) or priority not in EMAIL_PRIORITIES:
        return None
    category = item.get("category")
    if category not in EMAIL_CATEGORIES:
        return None
    area = item.get("area")
    if area is not None and area not in AREA_NAMES:
        area = None
    needs_reply = item.get("needs_reply")
    if not isinstance(needs_reply, bool):
        return None
    summary = item.get("one_line_summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    return {
        "id": email_id,
        "priority": priority,
        "category": category,
        "area": area,
        "needs_reply": needs_reply,
        "one_line_summary": " ".join(summary.split())[:300],
    }


def ai_enabled() -> bool:
    flags = get_setting("ai_enabled") or {}
    return bool(isinstance(flags, dict) and flags.get("mail_classify", False))


def call_claude(batch: list[dict]) -> dict[str, dict]:
    """Call D's classify_emails and return {id: validated item}. Empty on any failure."""
    if not batch or not ai_enabled():
        return {}
    fn = getattr(claude_client, "classify_emails", None)
    if fn is None:
        return {}
    try:
        result = fn(batch)
    except Exception as exc:
        log.warning("classify_emails raised, using rules: %s", exc)
        return {}
    if not isinstance(result, list):
        return {}
    allowed = {item["id"] for item in batch}
    out: dict[str, dict] = {}
    for raw in result:
        cleaned = validate_item(raw, allowed)
        if cleaned is not None:
            out[cleaned["id"]] = cleaned
    return out


def _area_ids() -> dict[str, object]:
    return {a.name: a.id for a in db.session.scalars(select(Area)).all()}


def apply_result(email: Email, item: dict, classifier: str, area_ids: dict, when: datetime) -> None:
    """Write raw classification columns only. Overrides are untouched by design."""
    email.priority = item["priority"]
    email.category = item["category"]
    email.area_id = area_ids.get(item["area"]) if item.get("area") else None
    email.needs_reply = bool(item["needs_reply"])
    email.summary = item["one_line_summary"]
    email.classifier = classifier
    email.classified_at = when


def classify_batch(emails: list[Email]) -> dict:
    if not emails:
        return {"claude": 0, "rules": 0}
    batch = build_batch(emails)
    from_claude = call_claude(batch)
    rules = {item["id"]: item for item in classify_rules(batch)}
    area_ids = _area_ids()
    when = now_utc()
    counts = {"claude": 0, "rules": 0}
    for email in emails:
        key = str(email.id)
        if key in from_claude:
            apply_result(email, from_claude[key], "claude", area_ids, when)
            counts["claude"] += 1
        else:
            apply_result(email, rules[key], "rules", area_ids, when)
            counts["rules"] += 1
    db.session.commit()
    return counts


def classify_pending(limit: int | None = None) -> dict:
    """Classify every email with classified_at IS NULL, in batches. Returns counts."""
    from ..modules.mail import service

    batch_size = int(get_setting("mail_classify_batch") or 15)
    batch_size = max(1, min(batch_size, 50))
    total = {"claude": 0, "rules": 0}
    done = 0
    while True:
        remaining = None if limit is None else limit - done
        if remaining is not None and remaining <= 0:
            break
        take = batch_size if remaining is None else min(batch_size, remaining)
        emails = service.unclassified(take)
        if not emails:
            break
        counts = classify_batch(emails)
        total["claude"] += counts["claude"]
        total["rules"] += counts["rules"]
        done += len(emails)
    return {"classified": done, "by": f"claude {total['claude']}, rules {total['rules']}"}


def reclassify(emails: list[Email]) -> dict:
    """Force a fresh classification. Overrides survive because they live in their own columns."""
    for email in emails:
        email.classified_at = None
    db.session.commit()
    return classify_batch(emails)
