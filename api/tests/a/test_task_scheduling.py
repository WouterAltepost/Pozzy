from datetime import datetime
from zoneinfo import ZoneInfo

from app.integrations import claude_client
from app.services import calendar_read, calendar_write

TZ = ZoneInfo("Europe/Amsterdam")


def _task(client, headers, **kw):
    body = {"title": "Deep work", "important": True, "estimated_minutes": 90, "due_date": "2026-09-16"}
    body.update(kw)
    return client.post("/api/tasks", json=body, headers=headers).get_json()["data"]


def test_suggest_slot_deterministic_fallback(client, headers):
    task = _task(client, headers)
    res = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers)
    assert res.status_code == 200, res.get_json()
    data = res.get_json()["data"]
    assert data["ranked_by"] == "deterministic"
    assert data["duration_minutes"] == 90
    assert len(data["slots"]) == 3
    assert data["slots"][0]["start"] == "2026-09-14T08:00:00+02:00"
    assert data["slots"][0]["end"] == "2026-09-14T09:30:00+02:00"
    assert [s["start"][:10] for s in data["slots"]] == ["2026-09-14", "2026-09-15", "2026-09-16"]
    assert all(s["reason"] for s in data["slots"])


def test_suggest_slot_uses_calendar_events_and_other_scheduled_tasks(client, headers, monkeypatch):
    def fake_events(start, end):
        return [(datetime(2026, 9, 14, 8, 0, tzinfo=TZ), datetime(2026, 9, 14, 12, 0, tzinfo=TZ))]

    monkeypatch.setattr(calendar_read, "get_events_between", fake_events)
    other = _task(client, headers, title="Other")
    client.post(f"/api/tasks/{other['id']}/schedule", json={"start": "2026-09-14T12:00:00+02:00", "end": "2026-09-14T14:00:00+02:00"}, headers=headers)

    task = _task(client, headers)
    data = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00", "duration_minutes": 60}, headers=headers).get_json()["data"]
    assert data["duration_minutes"] == 60
    assert data["slots"][0]["start"] == "2026-09-14T14:00:00+02:00"


def test_suggest_slot_claude_ranking_is_validated_against_candidates(client, headers, monkeypatch):
    task = _task(client, headers)
    seen = {}

    def fake_rank(task_dict, candidates, context=None):
        seen["candidates"] = candidates
        invented = {"start": "2026-09-14T03:00:00+02:00", "end": "2026-09-14T04:30:00+02:00", "reason": "made up"}
        real = dict(candidates[2], reason="Claude says so")
        return [invented, real]

    monkeypatch.setattr(claude_client, "rank_slots", fake_rank)
    data = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers).get_json()["data"]
    assert data["ranked_by"] == "claude"
    assert len(data["slots"]) == 1
    assert data["slots"][0]["start"] == seen["candidates"][2]["start"]
    assert data["slots"][0]["reason"] == "Claude says so"
    assert len(seen["candidates"]) <= 12


def test_suggest_slot_claude_failure_falls_back(client, headers, monkeypatch):
    task = _task(client, headers)

    def boom(*a, **k):
        raise RuntimeError("api down")

    monkeypatch.setattr(claude_client, "rank_slots", boom)
    data = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers).get_json()["data"]
    assert data["ranked_by"] == "deterministic" and len(data["slots"]) == 3


def test_suggest_slot_respects_kill_switch(client, headers, monkeypatch):
    client.put("/api/settings", json={"ai_enabled": {"scheduling": False}}, headers=headers)
    called = []
    monkeypatch.setattr(claude_client, "rank_slots", lambda *a, **k: called.append(1))
    task = _task(client, headers)
    client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers)
    assert called == []


def test_schedule_and_unschedule(client, headers, monkeypatch):
    monkeypatch.setattr(calendar_write, "create_event", lambda task: "uid-123")
    deleted = []
    monkeypatch.setattr(calendar_write, "delete_event", lambda task: deleted.append(task.calendar_uid) or True)
    task = _task(client, headers)
    res = client.post(f"/api/tasks/{task['id']}/schedule", json={"start": "2026-09-15T09:00:00+02:00"}, headers=headers)
    data = res.get_json()["data"]
    assert data["status"] == "scheduled"
    assert data["scheduled_start"] == "2026-09-15T09:00:00+02:00"
    assert data["scheduled_end"] == "2026-09-15T10:30:00+02:00"  # estimated_minutes 90
    assert data["calendar_uid"] == "uid-123"

    assert client.post(f"/api/tasks/{task['id']}/schedule", json={"start": "2026-09-15T09:00:00+02:00", "end": "2026-09-15T08:00:00+02:00"}, headers=headers).status_code == 400
    assert client.post(f"/api/tasks/{task['id']}/schedule", json={}, headers=headers).status_code == 400

    data = client.post(f"/api/tasks/{task['id']}/unschedule", headers=headers).get_json()["data"]
    assert data["status"] == "todo" and data["scheduled_start"] is None and data["calendar_uid"] is None
    assert deleted == ["uid-123"]


def test_schedule_survives_calendar_write_failure(client, headers, monkeypatch):
    def boom(task):
        raise RuntimeError("icloud 503")

    monkeypatch.setattr(calendar_write, "create_event", boom)
    task = _task(client, headers)
    data = client.post(f"/api/tasks/{task['id']}/schedule", json={"start": "2026-09-15T09:00:00+02:00"}, headers=headers).get_json()["data"]
    assert data["status"] == "scheduled" and data["calendar_uid"] is None
