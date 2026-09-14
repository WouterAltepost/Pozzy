from flask import Blueprint, request

from ...auth import require_auth
from ...errors import fail, ok
from ...models.email import EMAIL_CATEGORIES
from ...utils.validation import register_validation_handler, to_uuid
from . import service
from .schemas import parse_account_patch, parse_email_patch, parse_task_overrides

bp = Blueprint("mail", __name__, url_prefix="/api/mail")
register_validation_handler(bp)


def _not_found(what="Email"):
    return fail("not_found", f"{what} not found", 404)


def _tri(value: str | None):
    """'1'/'true' -> True, '0'/'false' -> False, 'all'/'' -> None."""
    if value in ("1", "true"):
        return True
    if value in ("0", "false"):
        return False
    return None


@bp.get("/emails")
@require_auth
def list_emails():
    args = request.args
    category = args.get("category") or None
    if category and category not in EMAIL_CATEGORIES:
        return fail("validation_error", "Unknown category", 400)
    priority = args.get("priority")
    if priority and priority not in ("1", "2", "3", "4"):
        return fail("validation_error", "priority must be 1-4", 400)
    handled = _tri(args.get("handled", "0"))
    try:
        limit = max(1, min(int(args.get("limit", 200)), 500))
        offset = max(0, int(args.get("offset", 0)))
    except ValueError:
        return fail("validation_error", "limit and offset must be integers", 400)
    rows = service.list_emails(
        account_id=to_uuid(args.get("account_id")) if args.get("account_id") else None,
        category=category,
        area_id=to_uuid(args.get("area_id")) if args.get("area_id") else None,
        needs_reply=_tri(args.get("needs_reply")),
        handled=handled,
        priority=int(priority) if priority else None,
        q=args.get("q") or None,
        limit=limit,
        offset=offset,
    )
    return ok([e.to_dict() for e in rows])


@bp.get("/counts")
@require_auth
def counts():
    return ok(service.counts())


@bp.get("/top")
@require_auth
def top():
    try:
        limit = max(1, min(int(request.args.get("limit", 0) or 0), 20)) or None
    except ValueError:
        limit = None
    return ok([e.to_dict() for e in service.top_emails(limit)])


@bp.get("/emails/<email_id>")
@require_auth
def get_email(email_id):
    email = service.get_email(email_id)
    if email is None:
        return _not_found()
    data = email.to_dict(with_snippet=True)
    task = service.task_for_email(email)
    data["task_id"] = str(task.id) if task else None
    return ok(data)


@bp.patch("/emails/<email_id>")
@require_auth
def update_email(email_id):
    email = service.get_email(email_id)
    if email is None:
        return _not_found()
    fields = parse_email_patch(request.get_json(silent=True))
    return ok(service.update_email(email, fields).to_dict(with_snippet=True))


@bp.post("/emails/<email_id>/task")
@require_auth
def create_task(email_id):
    email = service.get_email(email_id)
    if email is None:
        return _not_found()
    overrides = parse_task_overrides(request.get_json(silent=True))
    task, created = service.create_task_from_email(email, overrides)
    return ok({"task": task.to_dict(), "created": created}, 201 if created else 200)


@bp.post("/emails/<email_id>/reclassify")
@require_auth
def reclassify(email_id):
    from ...services import mail_classify

    email = service.get_email(email_id)
    if email is None:
        return _not_found()
    mail_classify.reclassify([email])
    return ok(email.to_dict(with_snippet=True))


@bp.get("/accounts")
@require_auth
def list_accounts():
    return ok([a.to_dict() for a in service.upsert_accounts_from_env()])


@bp.patch("/accounts/<account_id>")
@require_auth
def update_account(account_id):
    account = service.get_account(account_id)
    if account is None:
        return _not_found("Account")
    fields = parse_account_patch(request.get_json(silent=True))
    return ok(service.update_account(account, fields).to_dict())


@bp.post("/accounts/<account_id>/test")
@require_auth
def test_account(account_id):
    account = service.get_account(account_id)
    if account is None:
        return _not_found("Account")
    try:
        status = service.test_account(account)
    except Exception as exc:
        return fail("imap_error", f"{type(exc).__name__}: {exc}"[:500], 502)
    return ok({"ok": True, **status, "account": account.to_dict()})


@bp.post("/sync")
@require_auth
def sync_now():
    """Synchronous sync plus classification of every enabled account. Same work as the job, no job_runs row."""
    from ...services import mail_classify

    results = service.sync_all()
    classified = mail_classify.classify_pending()
    return ok({"accounts": results, "classified": classified, "counts": service.counts()})
