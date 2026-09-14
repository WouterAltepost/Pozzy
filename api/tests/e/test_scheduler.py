from app import scheduler as sched
from app.extensions import scheduler


def test_scheduler_not_started_in_tests(app):
    assert scheduler.running is False
    assert sched.scheduler_enabled(app) is False


def test_register_jobs_lists_every_job_from_jobs_md(app):
    ids = sched.register_jobs(app)
    expected = {"calendar_sync", "mail_sync_and_classify", "three_do_rollover", "deadline_urgency", "daily_briefing", "weekly_review_draft", "ai_cost_rollup"}
    assert set(ids) == expected
    assert {j.id for j in scheduler.get_jobs()} == expected
    briefing = scheduler.get_job("daily_briefing")
    assert str(briefing.trigger).startswith("cron[")
    # Registering twice replaces instead of duplicating.
    sched.register_jobs(app)
    assert len(scheduler.get_jobs()) == 7
    for j in scheduler.get_jobs():
        scheduler.remove_job(j.id)
    assert scheduler.running is False


def test_briefing_cron_follows_settings(app, client, token_factory):
    from conftest import bearer

    client.put("/api/settings", json={"briefing_time": "06:30"}, headers=bearer(token_factory()))
    assert sched._briefing_cron(app) == "30 6 * * *"


def test_start_guard(app, monkeypatch):
    monkeypatch.setattr(sched, "_started", True)
    assert sched.start_scheduler(app) is False


def test_health_reports_scheduler(client):
    data = client.get("/api/health").get_json()["data"]
    assert data["scheduler"]["running"] is False
    assert isinstance(data["scheduler"]["jobs"], list)
