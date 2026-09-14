from sqlalchemy import select

from app.extensions import db
from app.jobs import mail_sync
from app.models import Email, JobRun, MailAccount
from app.modules.mail import service


def _rows():
    return db.session.scalars(select(Email).order_by(Email.uid)).all()


def test_accounts_are_upserted_from_env(mail_env):
    accounts = service.upsert_accounts_from_env()
    assert [a.label for a in accounts] == ["Mail 1", "Personal", "Important", "Work"]
    assert all(a.secret_ref == f"env:{a.email}" for a in accounts)
    assert all(a.enabled for a in accounts)

    # Second run keeps the same rows and does not reset local state.
    accounts[1].enabled = False
    accounts[1].last_uid = 999
    db.session.commit()
    again = service.upsert_accounts_from_env()
    assert len(again) == 4
    assert {a.id for a in again} == {a.id for a in accounts}
    personal = next(a for a in again if a.email == "two@gmail.com")
    assert personal.enabled is False and personal.last_uid == 999


def test_env_missing_or_malformed_is_harmless(app):
    app.config["MAIL_ACCOUNTS_JSON"] = None
    assert service.upsert_accounts_from_env() == []
    app.config["MAIL_ACCOUNTS_JSON"] = "{not json"
    assert service.upsert_accounts_from_env() == []


def test_sync_four_accounts_twice_is_idempotent(server):
    first = service.sync_all(fetcher=server.fetch_new)
    assert [r["inserted"] for r in first] == [2, 1, 1, 1]
    assert all(r["error"] is None for r in first)
    assert len(_rows()) == 5
    # First run per account is a backfill (no last_uid yet).
    assert all(c["last_uid"] is None for c in server.calls)

    second = service.sync_all(fetcher=server.fetch_new)
    assert [r["inserted"] for r in second] == [0, 0, 0, 0]
    assert len(_rows()) == 5
    # Second run is incremental from the stored last_uid.
    assert {c["email"]: c["last_uid"] for c in server.calls[4:]} == {
        "one@gmail.com": 102,
        "two@gmail.com": 201,
        "three@gmail.com": 301,
        "work@alpacaai.nl": 401,
    }
    accounts = {a.email: a for a in service.list_accounts()}
    assert accounts["one@gmail.com"].last_uid == 102
    assert accounts["one@gmail.com"].last_synced_at is not None
    assert accounts["one@gmail.com"].last_error is None


def test_sync_stores_headers_snippet_labels_and_fallback_date(server):
    service.sync_all(fetcher=server.fetch_new)
    by_uid = {e.uid: e for e in _rows()}
    shipped = by_uid[102]
    assert shipped.labels == ["\\Inbox", "Shopping"]
    assert shipped.snippet.startswith("Shipped!")
    assert shipped.from_email == "noreply@shop.example"
    nodate = by_uid[401]
    assert nodate.date is not None  # sync time substituted
    assert nodate.subject == "Statement ready"
    multi = by_uid[101]
    assert multi.has_attachments is True
    assert "JVBERi" not in multi.snippet
    assert len(multi.snippet.encode("utf-8")) <= 2048
    assert multi.classified_at is None and multi.priority is None


def test_new_message_is_picked_up_incrementally(server):
    from tests.c.conftest import RAW_NO_DATE

    service.sync_all(fetcher=server.fetch_new)
    server.add("one@gmail.com", RAW_NO_DATE, 103)
    results = service.sync_all(fetcher=server.fetch_new)
    assert results[0]["inserted"] == 1
    assert len(_rows()) == 6
    account = next(a for a in service.list_accounts() if a.email == "one@gmail.com")
    assert account.last_uid == 103


def test_one_failing_account_does_not_stop_the_others(server):
    server.fail_for.add("two@gmail.com")
    results = service.sync_all(fetcher=server.fetch_new)
    failed = next(r for r in results if r["label"] == "Personal")
    assert "simulated IMAP failure" in failed["error"]
    assert sum(r["inserted"] for r in results) == 4
    account = next(a for a in service.list_accounts() if a.email == "two@gmail.com")
    assert "simulated IMAP failure" in account.last_error
    assert account.last_uid is None


def test_disabled_account_is_skipped(server):
    accounts = service.upsert_accounts_from_env()
    accounts[3].enabled = False
    db.session.commit()
    results = service.sync_all(fetcher=server.fetch_new)
    assert [r["label"] for r in results] == ["Mail 1", "Personal", "Important"]


def test_missing_password_is_recorded_not_raised(app, mail_env):
    accounts = service.upsert_accounts_from_env()
    row = accounts[0]
    row.email = "nobody@gmail.com"
    db.session.commit()
    result = service.sync_account(row, fetcher=lambda *a, **k: [])
    assert "No password" in result["error"]


def test_job_writes_job_run_and_survives_account_failure(app, server, monkeypatch):
    server.fail_for.add("work@alpacaai.nl")
    monkeypatch.setattr(service.imap_client, "fetch_new", server.fetch_new)
    message = mail_sync.run(app)
    assert "Mail 1: +2/2" in message
    assert "Work: ERROR" in message
    run = db.session.scalar(select(JobRun).where(JobRun.name == "mail_sync_and_classify"))
    assert run is not None and run.ok is True and run.finished_at is not None
    assert len(_rows()) == 4


def test_job_fails_when_every_account_fails(app, server, monkeypatch):
    server.fail_for.update(server.inbox.keys())
    monkeypatch.setattr(service.imap_client, "fetch_new", server.fetch_new)
    message = mail_sync.run(app)
    assert message.startswith("RuntimeError: all accounts failed")
    run = db.session.scalar(select(JobRun).where(JobRun.name == "mail_sync_and_classify"))
    assert run.ok is False
    # Per-account errors were still committed before the job-level failure.
    assert all(a.last_error for a in db.session.scalars(select(MailAccount)).all())
