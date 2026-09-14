"""classify_emails per stream C's contract: batching, validation, cache marker, kill switch, partial failure."""
import json

from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.models import AiCall


def _batch(n, prefix="e"):
    return [{"id": f"{prefix}{i}", "account_label": "Work", "from_name": "Alice", "from_email": "alice@client.com", "subject": f"Subject {i}", "date": "2026-09-14T10:15:00+02:00", "snippet": "Hi Wout, invoice?"} for i in range(n)]


def _reply_for(chunk, **overrides):
    return json.dumps({"results": [{"id": e["id"], "priority": 2, "category": "client", "area": "Work", "needs_reply": True, "one_line_summary": f"Alice asks about {e['subject']}.", **overrides} for e in chunk]})


def test_batches_of_15_on_fast_model_with_cached_system(app, fake_claude):
    batch = _batch(32)
    fake_claude.replies = [_reply_for(batch[0:15]), _reply_for(batch[15:30]), _reply_for(batch[30:32])]
    out = claude_client.classify_emails(batch)
    assert len(out) == 32 and out[0] == {"id": "e0", "priority": 2, "category": "client", "area": "Work", "needs_reply": True, "one_line_summary": "Alice asks about Subject 0."}
    assert len(fake_claude.calls) == 3
    for call in fake_claude.calls:
        assert call["model"] == app.config["CLAUDE_MODEL_FAST"]
        assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    sent = json.loads(fake_claude.calls[0]["messages"][0]["content"].split("\n\nReply exactly")[0])
    assert [e["id"] for e in sent["emails"]] == [f"e{i}" for i in range(15)]
    rows = db.session.scalars(select(AiCall)).all()
    assert len(rows) == 3 and all(r.feature == "classify_emails" and r.ok for r in rows)


def test_invalid_items_dropped(app, fake_claude):
    batch = _batch(6)
    fake_claude.reply = json.dumps({"results": [
        {"id": "e0", "priority": 1, "category": "Client", "area": "work", "needs_reply": False, "one_line_summary": "ok"},
        {"id": "e1", "priority": 7, "category": "client", "area": None, "needs_reply": False, "one_line_summary": "bad priority"},
        {"id": "e2", "priority": 3, "category": "spam", "area": None, "needs_reply": False, "one_line_summary": "bad category"},
        {"id": "e3", "priority": 3, "category": "other", "area": "Mars", "needs_reply": True, "one_line_summary": "area cleared"},
        {"id": "e4", "priority": 3, "category": "other", "area": None, "needs_reply": False, "one_line_summary": "  "},
        {"id": "nope", "priority": 3, "category": "other", "area": None, "needs_reply": False, "one_line_summary": "unknown id"},
        {"id": "e0", "priority": 4, "category": "other", "area": None, "needs_reply": False, "one_line_summary": "duplicate id"},
    ]})
    out = claude_client.classify_emails(batch)
    assert [(o["id"], o["category"], o["area"], o["priority"]) for o in out] == [("e0", "client", "Work", 1), ("e3", "other", None, 3)]


def test_partial_failure_returns_partial_and_total_failure_none(app, fake_claude):
    batch = _batch(20)
    fake_claude.replies = ["garbage", _reply_for(batch[15:20])]
    out = claude_client.classify_emails(batch)
    assert [o["id"] for o in out] == [f"e{i}" for i in range(15, 20)]
    fake_claude.reply = "garbage"
    assert claude_client.classify_emails(_batch(3)) is None
    assert claude_client.classify_emails([]) is None


def test_kill_switch_and_batch_setting(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"mail_classify": False}}, headers=headers)
    assert claude_client.classify_emails(_batch(3)) is None and fake_claude.calls == []
    client.put("/api/settings", json={"ai_enabled": {"mail_classify": True}, "mail_classify_batch": 4}, headers=headers)
    batch = _batch(9)
    fake_claude.replies = [_reply_for(batch[0:4]), _reply_for(batch[4:8]), _reply_for(batch[8:9])]
    assert len(claude_client.classify_emails(batch)) == 9 and len(fake_claude.calls) == 3
