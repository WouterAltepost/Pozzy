"""Daily briefing: context from A's tables, Claude text with deterministic fallback, job idempotency."""
import json
from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.jobs import daily_briefing as job
from app.models import AiCall, DailyBriefing, JobRun
from app.modules.ai import briefing


def _seed(client, headers, today):
    client.post("/api/tasks", json={"title": "Overdue thing", "due_date": "2000-01-01"}, headers=headers)
    client.post("/api/tasks", json={"title": "Due today", "due_date": today.isoformat(), "urgent": True, "important": True}, headers=headers)
    client.post("/api/dos", json={"date": today.isoformat(), "title": "Write briefing tests"}, headers=headers)
    client.post("/api/goals", json={"title": "Ship D"}, headers=headers)
    client.post("/api/trackers", json={"name": "Creatine", "type": "daily_bool"}, headers=headers)


def test_context_collects_facts(client, headers, fake_claude):
    today = date.today()
    _seed(client, headers, today)
    ctx = briefing.build_context(today)
    assert ctx["date"] == today.isoformat() and ctx["weekday"] in briefing.WEEKDAYS
    assert {t["title"] for t in ctx["tasks_due"]} == {"Overdue thing", "Due today"}
    assert next(t for t in ctx["tasks_due"] if t["title"] == "Overdue thing")["overdue"] is True
    assert ctx["dos"] == [{"title": "Write briefing tests", "done": False, "rolled": False}]
    assert ctx["weekly_goals"][0]["title"] == "Ship D"
    assert ctx["trackers_open"][0]["name"] == "Creatine"
    assert ctx["events"] == [] and ctx["emails"] == []


def test_deterministic_text_mentions_facts(client, headers):
    today = date.today()
    _seed(client, headers, today)
    text = briefing.deterministic_text(briefing.build_context(today))
    assert "Overdue: Overdue thing" in text and "Due today: Due today" in text and "Creatine" in text and "Write briefing tests" in text


def test_generate_uses_claude_and_stores_row(client, headers, fake_claude):
    fake_claude.reply = json.dumps({"text": "Quiet day. Finish the overdue thing first."})
    data = client.post("/api/ai/briefing", headers=headers).get_json()["data"]
    assert data["source"] == "claude" and data["text"].startswith("Quiet day") and data["model"] == "claude-sonnet-4-5"
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["date"] == date.today().isoformat() and "tasks_due" in sent
    assert client.get("/api/ai/briefing", headers=headers).get_json()["data"]["id"] == data["id"]
    row = db.session.scalar(select(DailyBriefing))
    assert row.context_json["date"] == date.today().isoformat()
    assert db.session.scalar(select(AiCall)).feature == "daily_briefing"


def test_generate_falls_back_without_ai(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"briefing": False}}, headers=headers)
    data = client.post("/api/ai/briefing", json={"date": "2026-09-16"}, headers=headers).get_json()["data"]
    assert data["source"] == "deterministic" and data["date"] == "2026-09-16" and "Wednesday 2026-09-16" in data["text"]
    assert fake_claude.calls == []
    fake_claude.reply = "garbage"
    client.put("/api/settings", json={"ai_enabled": {"briefing": True}}, headers=headers)
    data = client.post("/api/ai/briefing", json={"date": "2026-09-16"}, headers=headers).get_json()["data"]
    assert data["source"] == "deterministic" and len(fake_claude.calls) == 1
    assert db.session.scalar(select(db.func.count()).select_from(DailyBriefing)) == 1


def test_get_returns_null_when_missing_and_context_endpoint(client, headers):
    assert client.get("/api/ai/briefing?date=2030-01-01", headers=headers).get_json()["data"] is None
    assert client.get("/api/ai/briefing/context?date=2030-01-01", headers=headers).get_json()["data"]["date"] == "2030-01-01"
    assert client.get("/api/ai/briefing").status_code == 401
    assert client.get("/api/ai/briefing?date=nope", headers=headers).status_code == 400


def test_job_is_idempotent_and_logs(app, fake_claude):
    fake_claude.reply = json.dumps({"text": "Morning."})
    msg1 = job.run(app)
    msg2 = job.run(app)
    assert "generated (claude)" in msg1 and "already existed" in msg2
    assert len(fake_claude.calls) == 1
    runs = db.session.scalars(select(JobRun).where(JobRun.name == "daily_briefing")).all()
    assert len(runs) == 2 and all(r.ok for r in runs)


def test_job_never_raises(app, fake_claude, monkeypatch):
    monkeypatch.setattr(briefing, "build_context", lambda day=None: 1 / 0)
    msg = job.run(app)
    assert "ZeroDivisionError" in msg
    run = db.session.scalar(select(JobRun).where(JobRun.name == "daily_briefing"))
    assert run.ok is False
