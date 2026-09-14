"""Mail business logic (stream C): accounts from env, IMAP sync, inbox queries, actions.

The sync job and the routes call these functions. Other modules (D's review
stats, the homepage widget) read through `list_emails`/`top_emails`.
"""
import json
import logging
import uuid
from datetime import datetime

from flask import current_app
from sqlalchemy import and_, or_, select

from ...extensions import db
from ...integrations import imap_client
from ...models import Area, Email, MailAccount
from ...models.email import EMAIL_CATEGORIES, EMAIL_PRIORITIES
from ...settings_defaults import get_setting
from ...utils.dates import now_utc
from ...utils.validation import ValidationError

log = logging.getLogger(__name__)

PRIORITY_ORDER = {1: 0, 2: 1, 3: 2, 4: 3}


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def env_accounts() -> list[dict]:
    """Parse MAIL_ACCOUNTS_JSON. Returns [] when unset or malformed (logged, never raised)."""
    raw = current_app.config.get("MAIL_ACCOUNTS_JSON")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        log.error("MAIL_ACCOUNTS_JSON is not valid JSON: %s", exc)
        return []
    if not isinstance(data, list):
        log.error("MAIL_ACCOUNTS_JSON must be a JSON array")
        return []
    out = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        email = (entry.get("email") or "").strip().lower()
        if not email:
            continue
        out.append(
            {
                "email": email,
                "label": (entry.get("label") or email.split("@", 1)[0])[:60],
                "password": entry.get("password") or "",
                "color": entry.get("color") or None,
                "imap_host": entry.get("imap_host") or imap_client.DEFAULT_HOST,
            }
        )
    return out


def upsert_accounts_from_env() -> list[MailAccount]:
    """Upsert mail_accounts rows by email from MAIL_ACCOUNTS_JSON.

    Label, colour, host and secret_ref follow the env; `enabled`, `last_uid`
    and sort order are kept once the row exists so the UI stays in control.
    """
    entries = env_accounts()
    if not entries:
        return list_accounts()
    existing = {a.email: a for a in db.session.scalars(select(MailAccount)).all()}
    for index, entry in enumerate(entries):
        row = existing.get(entry["email"])
        if row is None:
            row = MailAccount(email=entry["email"], enabled=True, sort_order=index)
            db.session.add(row)
            existing[entry["email"]] = row
        row.label = entry["label"]
        row.color = entry["color"]
        row.imap_host = entry["imap_host"]
        row.secret_ref = f"env:{entry['email']}"
    # Rows whose address is no longer in the env (a typo fixed, an account removed) have no
    # password to sync with; disable them so every job run does not report a failing account.
    env_emails = {entry["email"] for entry in entries}
    for email, row in existing.items():
        if email not in env_emails and row.enabled:
            row.enabled = False
            row.last_error = "Not in MAIL_ACCOUNTS_JSON, disabled"
    db.session.commit()
    return list_accounts()


def list_accounts() -> list[MailAccount]:
    return db.session.scalars(select(MailAccount).order_by(MailAccount.sort_order, MailAccount.label)).all()


def get_account(account_id) -> MailAccount | None:
    try:
        return db.session.get(MailAccount, uuid.UUID(str(account_id)))
    except (ValueError, TypeError):
        return None


def update_account(account: MailAccount, fields: dict) -> MailAccount:
    for key, value in fields.items():
        setattr(account, key, value)
    db.session.commit()
    return account


def resolve_password(account: MailAccount) -> str | None:
    """Look the password up in MAIL_ACCOUNTS_JSON. Only `env:` secret refs exist in v1."""
    for entry in env_accounts():
        if entry["email"] == account.email.lower():
            return entry["password"] or None
    return None


def test_account(account: MailAccount) -> dict:
    """Live connection test. Records the outcome on the row. Raises on failure."""
    password = resolve_password(account)
    if not password:
        account.last_error = "No password for this account in MAIL_ACCOUNTS_JSON"
        db.session.commit()
        raise ValidationError(account.last_error)
    try:
        status = imap_client.test_login(account.email, password, account.imap_host)
    except Exception as exc:
        account.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        db.session.commit()
        raise
    account.last_error = None
    db.session.commit()
    return status


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_account(account: MailAccount, fetcher=None) -> dict:
    """Fetch INBOX messages with UID > last_uid and insert the new ones.

    Idempotent: rows are keyed on (account_id, uid), existing ones are skipped.
    Failures are recorded in `last_error` and returned, never raised, so one
    account cannot stop the others.
    """
    fetcher = fetcher or imap_client.fetch_new
    result = {"account_id": str(account.id), "label": account.label, "fetched": 0, "inserted": 0, "error": None}
    password = resolve_password(account)
    if not password:
        account.last_error = "No password for this account in MAIL_ACCOUNTS_JSON"
        db.session.commit()
        result["error"] = account.last_error
        return result
    try:
        rows = fetcher(
            account.email,
            password,
            last_uid=account.last_uid,
            backfill_days=int(get_setting("mail_backfill_days") or 7),
            host=account.imap_host,
            max_messages=int(get_setting("mail_max_per_sync") or 500),
        )
    except Exception as exc:
        db.session.rollback()
        account.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        db.session.commit()
        log.warning("mail sync failed for %s: %s", account.email, account.last_error)
        result["error"] = account.last_error
        return result

    result["fetched"] = len(rows)
    inserted = _insert_rows(account, rows)
    result["inserted"] = inserted
    highest = max((r["uid"] for r in rows if r.get("uid")), default=None)
    if highest and (account.last_uid is None or highest > account.last_uid):
        account.last_uid = highest
    account.last_synced_at = now_utc()
    account.last_error = None
    db.session.commit()
    return result


def _insert_rows(account: MailAccount, rows: list[dict]) -> int:
    uids = [r["uid"] for r in rows if r.get("uid")]
    if not uids:
        return 0
    existing = set(
        db.session.scalars(select(Email.uid).where(Email.account_id == account.id, Email.uid.in_(uids))).all()
    )
    now = now_utc()
    inserted = 0
    seen = set()
    for r in rows:
        uid = r.get("uid")
        if not uid or uid in existing or uid in seen:
            continue
        seen.add(uid)
        db.session.add(
            Email(
                account_id=account.id,
                uid=uid,
                message_id=(r.get("message_id") or None),
                thread_hint=(r.get("thread_hint") or None),
                from_name=(r.get("from_name") or "")[:255],
                from_email=(r.get("from_email") or "")[:320],
                to_addrs=list(r.get("to_addrs") or []),
                subject=r.get("subject") or "(no subject)",
                date=r.get("date") or now,
                snippet=r.get("snippet") or "",
                labels=list(r.get("labels") or []),
                has_attachments=bool(r.get("has_attachments")),
            )
        )
        inserted += 1
    db.session.flush()
    return inserted


def sync_all(fetcher=None) -> list[dict]:
    """Upsert accounts from env, then sync every enabled account. Never raises per account."""
    accounts = upsert_accounts_from_env()
    return [sync_account(a, fetcher) for a in accounts if a.enabled]


# ---------------------------------------------------------------------------
# Inbox queries
# ---------------------------------------------------------------------------

def get_email(email_id) -> Email | None:
    try:
        return db.session.get(Email, uuid.UUID(str(email_id)))
    except (ValueError, TypeError):
        return None


def _effective_priority_expr():
    from sqlalchemy import func

    return func.coalesce(Email.priority_override, Email.priority, 3)


def list_emails(
    *,
    account_id=None,
    category: str | None = None,
    area_id=None,
    needs_reply: bool | None = None,
    handled: bool | None = False,
    priority: int | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Email]:
    """Unified inbox: all accounts, effective priority first, then newest."""
    from sqlalchemy import func

    prio = _effective_priority_expr()
    stmt = select(Email)
    if account_id:
        stmt = stmt.where(Email.account_id == account_id)
    if category:
        stmt = stmt.where(func.coalesce(Email.category_override, Email.category, "other") == category)
    if area_id:
        stmt = stmt.where(func.coalesce(Email.area_override_id, Email.area_id) == area_id)
    if needs_reply is not None:
        stmt = stmt.where(Email.needs_reply.is_(needs_reply))
    if handled is not None:
        stmt = stmt.where(Email.handled.is_(handled))
    if priority:
        stmt = stmt.where(prio == priority)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Email.subject.ilike(like), Email.from_name.ilike(like), Email.from_email.ilike(like), Email.summary.ilike(like)))
    stmt = stmt.order_by(prio.asc(), Email.date.desc()).offset(offset).limit(limit)
    return db.session.scalars(stmt).unique().all()


def top_emails(limit: int | None = None) -> list[Email]:
    limit = limit or int(get_setting("mail_top_count") or 5)
    return list_emails(handled=False, limit=limit)


def unclassified(limit: int) -> list[Email]:
    stmt = select(Email).where(Email.classified_at.is_(None)).order_by(Email.date.desc()).limit(limit)
    return db.session.scalars(stmt).unique().all()


def counts() -> dict:
    from sqlalchemy import func

    unhandled = db.session.scalar(select(func.count()).select_from(Email).where(Email.handled.is_(False))) or 0
    reply = db.session.scalar(
        select(func.count()).select_from(Email).where(Email.handled.is_(False), Email.needs_reply.is_(True))
    ) or 0
    pending = db.session.scalar(select(func.count()).select_from(Email).where(Email.classified_at.is_(None))) or 0
    return {"unhandled": int(unhandled), "needs_reply": int(reply), "unclassified": int(pending)}


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def update_email(email: Email, fields: dict) -> Email:
    """Apply handled flag and manual overrides. Overrides never touch the raw classification."""
    if "handled" in fields:
        email.handled = bool(fields["handled"])
        email.handled_at = now_utc() if email.handled else None
    if "priority_override" in fields:
        value = fields["priority_override"]
        if value is not None and value not in EMAIL_PRIORITIES:
            raise ValidationError("'priority_override' must be 1, 2, 3 or 4")
        email.priority_override = value
    if "category_override" in fields:
        value = fields["category_override"]
        if value is not None and value not in EMAIL_CATEGORIES:
            raise ValidationError("'category_override' must be one of: " + ", ".join(EMAIL_CATEGORIES))
        email.category_override = value
    if "area_override_id" in fields:
        value = fields["area_override_id"]
        if value is not None and db.session.get(Area, value) is None:
            raise ValidationError("'area_override_id' does not match an area")
        email.area_override_id = value
    db.session.commit()
    return email


def task_for_email(email: Email):
    from ...models import Task

    return db.session.scalar(select(Task).where(Task.source == "email", Task.source_ref == str(email.id)))


def create_task_from_email(email: Email, overrides: dict | None = None):
    """Create a task linked to the email via A's service function (not HTTP). Idempotent per email."""
    from ..tasks import service as tasks_service

    existing = task_for_email(email)
    if existing is not None:
        return existing, False

    sender = email.from_name or email.from_email
    lines = [f"From: {sender} <{email.from_email}>" if email.from_name else f"From: {email.from_email}"]
    if email.account is not None:
        lines.append(f"Account: {email.account.label}")
    if email.gmail_url:
        lines.append(f"Open in Gmail: {email.gmail_url}")
    if email.summary:
        lines.append("")
        lines.append(email.summary)

    fields = {
        "title": (email.subject or "(no subject)")[:200],
        "description": "\n".join(lines),
        "area_id": email.effective_area_id,
        "tags": ["email"],
        "urgent": email.effective_priority == 1,
        "important": email.effective_priority <= 2,
        "status": "todo",
        "source": "email",
        "source_ref": str(email.id),
    }
    for key in ("title", "description", "area_id", "urgent", "important", "due_date", "estimated_minutes", "tags"):
        if overrides and key in overrides:
            fields[key] = overrides[key]
    task = tasks_service.create_task(fields)
    return task, True
