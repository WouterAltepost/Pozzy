"""Push subscriptions and the habit_reminders job (no real push service is contacted)."""
from datetime import date, datetime, timezone

import pytest

from app.extensions import db
from app.models import JobRun, PushSubscription, Tracker


@pytest.fixture
def push(app, monkeypatch):
    app.config.update(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv")
    sent = []
    from app.integrations import webpush

    monkeypatch.setattr(webpush, "send", lambda sub, payload: sent.append(payload) or True)
    return sent


def _sub(client, headers, endpoint="https://push.example/1"):
    return client.post("/api/push/subscriptions", json={"endpoint": endpoint, "keys": {"p256dh": "k", "auth": "a"}}, headers=headers)


def test_subscriptions_and_test_send(client, headers, app, push):
    assert client.get("/api/push/config", headers=headers).get_json()["data"] == {"configured": True, "public_key": "pub", "subscriptions": 0}
    assert _sub(client, headers).status_code == 201
    assert _sub(client, headers).status_code == 201  # same endpoint upserts
    assert db.session.query(PushSubscription).count() == 1
    assert client.post("/api/push/subscriptions", json={"endpoint": "x"}, headers=headers).status_code == 400
    res = client.post("/api/push/test", headers=headers).get_json()["data"]
    assert res == {"subscriptions": 1, "sent": 1} and push[0]["title"] == "Pozzy"
    assert client.delete("/api/push/subscriptions", json={"endpoint": "https://push.example/1"}, headers=headers).get_json()["data"]["deleted"] is True
    app.config.update(VAPID_PRIVATE_KEY=None)
    assert client.post("/api/push/test", headers=headers).status_code == 409


def _run_at(app, monkeypatch, hh, mm, day=date(2026, 10, 15)):
    from app.jobs import habit_reminders

    # 2026-10-15 is CEST (UTC+2).
    monkeypatch.setattr(habit_reminders, "now_fn", lambda: datetime(day.year, day.month, day.day, hh - 2, mm, tzinfo=timezone.utc))
    return habit_reminders.run(app)


def test_job_reminds_once_only_when_due_and_open(client, headers, app, push, monkeypatch):
    _sub(client, headers)
    mk = lambda **kw: client.post("/api/trackers", json={"type": "daily_bool", **kw}, headers=headers).get_json()["data"]
    creatine = mk(name="Creatine", reminder_time="08:00")
    mk(name="Gym", reminder_time="08:00", schedule="weekdays", schedule_days=0b0000001)  # Mondays only; the 15th is a Thursday
    read = mk(name="Read", reminder_time="08:00")
    mk(name="Late", reminder_time="21:00")
    client.post(f"/api/trackers/{read['id']}/tick", json={"date": "2026-10-15"}, headers=headers)

    assert "nothing to send (0 handled)" in _run_at(app, monkeypatch, 7, 55)
    msg = _run_at(app, monkeypatch, 8, 5)
    assert msg.startswith("reminded 1 habit(s) on 1 of 1")
    assert push[-1]["title"] == "Creatine"
    # Second run the same day sends nothing; Gym and Read were handled too.
    assert "nothing to send" in _run_at(app, monkeypatch, 8, 10)
    assert db.session.get(Tracker, __import__("uuid").UUID(creatine["id"])).last_reminded_on == date(2026, 10, 15)
    assert len(push) == 1
    # More than an hour late is dropped, not sent.
    client.patch(f"/api/trackers/{creatine['id']}", json={"reminder_time": "06:00"}, headers=headers)
    assert "nothing to send (1 handled)" in _run_at(app, monkeypatch, 8, 15)
    assert db.session.query(JobRun).filter_by(name="habit_reminders").count() == 4


def test_job_groups_several_and_respects_the_switch(client, headers, app, push, monkeypatch):
    _sub(client, headers)
    for name in ("A", "B"):
        client.post("/api/trackers", json={"type": "daily_bool", "name": name, "reminder_time": "09:00"}, headers=headers)
    client.put("/api/settings", json={"habit_reminders": False}, headers=headers)
    assert "switched off" in _run_at(app, monkeypatch, 9, 0)
    client.put("/api/settings", json={"habit_reminders": True}, headers=headers)
    _run_at(app, monkeypatch, 9, 0)
    assert push[-1]["title"] == "2 habits still open" and push[-1]["body"] == "A, B"
