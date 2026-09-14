"""AI spend summary endpoint and the nightly rollup job."""
from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.jobs import ai_cost_rollup as job
from app.models import AiCall, JobRun, Setting
from app.modules.ai import spend


def _seed(fake_claude):
    fake_claude.usage = {"input_tokens": 1000, "output_tokens": 100}
    claude_client.ping("a")  # 0.001 + 0.0005 = 0.0015 on haiku
    claude_client.ping("b")
    fake_claude.reply = "garbage"
    claude_client.ping("c")  # failed, still costs tokens


def test_totals_and_summary(client, headers, fake_claude):
    _seed(fake_claude)
    data = client.get("/api/ai/spend", headers=headers).get_json()["data"]
    assert data["month"]["calls"] == 3 and data["month"]["failed"] == 1
    assert data["month"]["cost"] == 0.0045 and data["today_cost"] == 0.0045
    assert data["month"]["by_feature"] == [{"feature": "smoke", "calls": 3, "failed": 1, "cost": 0.0045, "input_tokens": 3000, "output_tokens": 300}]
    assert data["month"]["by_model"][0]["model"] == "claude-haiku-4-5"
    assert len(data["last_7_days"]) == 7 and data["last_7_days"][-1]["calls"] == 3
    assert data["budget_usd"] == 10
    assert len(data["recent"]) == 3 and sum(1 for r in data["recent"] if r["error"]) == 1
    assert client.get("/api/ai/spend").status_code == 401


def test_empty_summary(client, headers):
    data = client.get("/api/ai/spend", headers=headers).get_json()["data"]
    assert data["month"]["cost"] == 0 and data["month"]["by_feature"] == [] and data["recent"] == []


def test_rollup_job_idempotent(app, fake_claude):
    _seed(fake_claude)
    msg = job.run(app)
    assert "3 call(s), 1 failed, $0.0045" in msg
    job.run(app)
    row = db.session.scalar(select(Setting).where(Setting.key == spend.ROLLUP_KEY))
    today = date.today().isoformat()
    assert list(row.value.keys()) == [today] and row.value[today]["by_feature"] == {"smoke": 0.0045}
    assert all(r.ok for r in db.session.scalars(select(JobRun).where(JobRun.name == "ai_cost_rollup")).all())


def test_rollup_prunes_old_days(app):
    db.session.add(Setting(key=spend.ROLLUP_KEY, value={"2000-01-01": {"cost": 1, "calls": 1, "failed": 0, "by_feature": {}}}))
    db.session.commit()
    spend.rollup_day(date.today())
    row = db.session.scalar(select(Setting).where(Setting.key == spend.ROLLUP_KEY))
    assert "2000-01-01" not in row.value and date.today().isoformat() in row.value
