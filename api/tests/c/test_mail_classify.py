import uuid

from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.models import Email, Setting
from app.modules.mail import service
from app.services import mail_classify


def _emails():
    return {e.uid: e for e in db.session.scalars(select(Email)).all()}


def _synced(server):
    service.sync_all(fetcher=server.fetch_new)
    return _emails()


def test_rules_fallback_runs_when_classify_emails_is_missing_or_returns_none(server, monkeypatch):
    _synced(server)
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    result = mail_classify.classify_pending()
    assert result == {"classified": 5, "by": "claude 0, rules 5"}
    rows = _emails()
    assert all(e.classifier == "rules" and e.classified_at is not None for e in rows.values())

    monkeypatch.delattr(claude_client, "classify_emails", raising=False)
    mail_classify.reclassify(list(rows.values()))
    assert all(e.classifier == "rules" for e in _emails().values())


def test_rules_heuristics(server, areas, monkeypatch):
    rows = _synced(server)
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    mail_classify.classify_pending()
    rows = _emails()
    assert rows[101].category == "finance"  # "invoice" in subject
    assert rows[101].priority == 3
    assert str(rows[101].area_id) == areas["Personal"]
    assert rows[102].category == "notification"  # noreply sender
    assert rows[102].priority == 4
    assert rows[201].category == "newsletter"  # tldr sender
    assert rows[201].priority == 4
    assert rows[301].category == "school"  # uni. sender and Prüfung subject
    assert str(rows[301].area_id) == areas["Study"]
    assert rows[401].category == "finance"  # bank@ sender, "statement" subject
    assert all(e.needs_reply is False for e in rows.values())
    assert rows[101].summary == "Invoice question"


def test_rules_use_work_account_as_client_signal():
    item = {"id": "x", "account_label": "Work", "from_email": "someone@bigcorp.example", "from_name": "", "subject": "Hello"}
    out = mail_classify.classify_rules_one(item)
    assert out["category"] == "client" and out["area"] == "Work" and out["priority"] == 3
    item["account_label"] = "Personal"
    assert mail_classify.classify_rules_one(item)["category"] == "other"
    item["from_email"] = "friend@gmail.com"
    assert mail_classify.classify_rules_one(item)["category"] == "personal"


def test_claude_results_are_validated_and_merged_with_rules(server, areas, monkeypatch):
    rows = _synced(server)
    target = str(rows[101].id)
    bogus = str(rows[102].id)

    def fake(batch):
        assert len(batch) <= 15
        assert {"id", "account_label", "from_name", "from_email", "subject", "date", "snippet"} <= set(batch[0])
        return [
            {"id": target, "priority": 1, "category": "client", "area": "Work", "needs_reply": True, "one_line_summary": "  Alice wants   the invoice. "},
            {"id": bogus, "priority": 7, "category": "client", "area": "Work", "needs_reply": True, "one_line_summary": "bad priority"},
            {"id": "not-an-id", "priority": 1, "category": "client", "area": "Work", "needs_reply": True, "one_line_summary": "unknown id"},
            {"id": str(rows[201].id), "priority": 4, "category": "newsletter", "area": "Mars", "needs_reply": "no", "one_line_summary": "bad bool"},
        ]

    monkeypatch.setattr(claude_client, "classify_emails", fake, raising=False)
    result = mail_classify.classify_pending()
    assert result["by"] == "claude 1, rules 4"
    rows = _emails()
    assert rows[101].classifier == "claude"
    assert rows[101].priority == 1 and rows[101].category == "client" and rows[101].needs_reply is True
    assert str(rows[101].area_id) == areas["Work"]
    assert rows[101].summary == "Alice wants the invoice."
    assert rows[102].classifier == "rules"
    assert rows[201].classifier == "rules"


def test_claude_exception_falls_back(server, monkeypatch):
    _synced(server)

    def boom(batch):
        raise RuntimeError("api down")

    monkeypatch.setattr(claude_client, "classify_emails", boom, raising=False)
    assert mail_classify.classify_pending()["by"] == "claude 0, rules 5"


def test_kill_switch_skips_claude(server, monkeypatch):
    _synced(server)
    called = []
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: called.append(1) or None, raising=False)
    flags = db.session.scalar(select(Setting).where(Setting.key == "ai_enabled"))
    flags.value = {**flags.value, "mail_classify": False}
    db.session.commit()
    mail_classify.classify_pending()
    assert called == []


def test_batches_respect_setting(server, monkeypatch):
    _synced(server)
    sizes = []
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: sizes.append(len(batch)) or None, raising=False)
    db.session.add(Setting(key="mail_classify_batch", value=2))
    db.session.commit()
    assert mail_classify.classify_pending()["classified"] == 5
    assert sizes == [2, 2, 1]


def test_overrides_survive_reclassification(server, areas, monkeypatch):
    rows = _synced(server)
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    mail_classify.classify_pending()
    email = _emails()[102]
    assert email.effective_priority == 4 and email.effective_category == "notification"

    service.update_email(email, {"priority_override": 1, "category_override": "client", "area_override_id": uuid.UUID(areas["Work"])})
    assert email.effective_priority == 1 and email.effective_category == "client"

    def fake(batch):
        return [{"id": str(email.id), "priority": 4, "category": "newsletter", "area": "Study", "needs_reply": False, "one_line_summary": "spam"}]

    monkeypatch.setattr(claude_client, "classify_emails", fake, raising=False)
    mail_classify.reclassify([email])
    db.session.refresh(email)
    assert email.priority == 4 and email.category == "newsletter" and email.classifier == "claude"
    assert email.priority_override == 1 and email.category_override == "client"
    assert email.effective_priority == 1 and email.effective_category == "client"
    assert str(email.effective_area_id) == areas["Work"]
    assert email.to_dict()["priority"] == 1
    assert email.to_dict()["raw"]["priority"] == 4
    assert email.to_dict()["overrides"]["priority"] == 1


def test_job_classifies_after_sync(app, server, monkeypatch):
    monkeypatch.setattr(service.imap_client, "fetch_new", server.fetch_new)
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    from app.jobs import mail_sync

    message = mail_sync.run(app)
    assert "classified 5 (claude 0, rules 5)" in message
    assert service.counts()["unclassified"] == 0
