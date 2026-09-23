"""Hours suggestions: past agenda events and completed tasks without a log, confirm or skip."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import CalendarAccount, CalendarEvent, HoursLog


def _account():
    acc = CalendarAccount(name="iCloud", caldav_url="https://caldav.example", username="w@example.com", secret_ref="ICLOUD_APP_PASSWORD", calendar_urls=["https://caldav.example/uni/"], known_calendars=[{"name": "Uni", "url": "https://caldav.example/uni/"}])
    db.session.add(acc)
    db.session.commit()
    return acc


def _event(acc, uid, start, minutes, calendar="https://caldav.example/uni/", title="Lecture", all_day=False, task_id=None, recurrence_id=""):
    ev = CalendarEvent(account_id=acc.id, calendar_url=calendar, uid=uid, recurrence_id=recurrence_id, title=title, start=start, end=start + timedelta(minutes=minutes), all_day=all_day, task_id=task_id)
    db.session.add(ev)
    db.session.commit()
    return ev


def test_suggestions_come_from_past_events_and_completed_tasks(client, headers, areas):
    acc = _account()
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    _event(acc, "lec-1", yesterday.replace(hour=9, minute=0), 90, title="Databases")
    _event(acc, "lec-2", yesterday.replace(hour=11, minute=0), 120, title="Tutorial", recurrence_id="20260101T110000")
    _event(acc, "future", now + timedelta(hours=2), 60, title="Later today")  # not over yet
    _event(acc, "short", yesterday.replace(hour=14, minute=0), 10, title="Ping")  # under 15 minutes
    _event(acc, "bday", yesterday, 60, title="Birthday", all_day=True)
    _event(acc, "old", now - timedelta(days=9), 60, title="Too old")
    _event(acc, "pozzy", yesterday.replace(hour=15, minute=0), 60, title="Task block", task_id=__import__("uuid").uuid4())

    # A calendar mapped to Study gives its events that area up front.
    client.put("/api/settings", json={"calendar_areas": {"https://caldav.example/uni/": areas["Study"]}}, headers=headers)

    # A task completed without an estimate: complete_task logged nothing, so it is suggested at the default length.
    task = client.post("/api/tasks", json={"title": "Write report", "area_id": areas["Work"]}, headers=headers).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/complete", headers=headers)
    # A task with an estimate was logged by complete_task itself and must not show up.
    est = client.post("/api/tasks", json={"title": "Estimated", "estimated_minutes": 30}, headers=headers).get_json()["data"]
    client.post(f"/api/tasks/{est['id']}/complete", headers=headers)

    data = client.get("/api/hours/suggestions", headers=headers).get_json()["data"]
    by_title = {i["title"]: i for i in data["items"]}
    assert set(by_title) == {"Databases", "Tutorial", "Write report"}
    assert by_title["Databases"]["minutes"] == 90 and by_title["Databases"]["area_name"] == "Study" and by_title["Databases"]["kind"] == "event"
    assert by_title["Tutorial"]["ref"] == "event:lec-2|20260101T110000"
    assert by_title["Write report"]["kind"] == "task" and by_title["Write report"]["minutes"] == 60 and by_title["Write report"]["area_name"] == "Work"
    assert data["total_minutes"] == 270
    assert data["per_area"][0] == {"area": "Study", "minutes": 210}

    # Accept two, skip one. Accepting twice does not double the hours.
    picks = [
        {"ref": by_title["Databases"]["ref"], "date": by_title["Databases"]["date"], "minutes": 90, "area_id": areas["Study"], "note": "Databases"},
        {"ref": by_title["Write report"]["ref"], "date": by_title["Write report"]["date"], "minutes": 45, "area_id": areas["Work"], "note": "Write report"},
    ]
    res = client.post("/api/hours/suggestions/accept", json={"items": picks}, headers=headers)
    assert res.status_code == 201, res.get_json()
    created = res.get_json()["data"]["created"]
    assert len(created) == 2 and {c["source_ref"] for c in created} == {picks[0]["ref"], picks[1]["ref"]}
    assert next(c for c in created if c["source_ref"].startswith("task:"))["task_id"] == task["id"]
    again = client.post("/api/hours/suggestions/accept", json={"items": picks}, headers=headers).get_json()["data"]
    assert again["created"] == []
    assert db.session.scalar(select(db.func.count()).select_from(HoursLog).where(HoursLog.source_ref.is_not(None))) == 3  # plus the estimated task

    assert client.post("/api/hours/suggestions/dismiss", json={"refs": [by_title["Tutorial"]["ref"]]}, headers=headers).get_json()["data"]["dismissed"] == 1
    assert client.post("/api/hours/suggestions/dismiss", json={"refs": [by_title["Tutorial"]["ref"]]}, headers=headers).get_json()["data"]["dismissed"] == 0
    assert client.get("/api/hours/suggestions", headers=headers).get_json()["data"]["items"] == []

    assert client.post("/api/hours/suggestions/accept", json={"items": []}, headers=headers).status_code == 400
    assert client.post("/api/hours/suggestions/accept", json={"items": [{"ref": "bogus:1", "minutes": 10}]}, headers=headers).status_code == 400
    assert client.post("/api/hours/suggestions/dismiss", json={"refs": "x"}, headers=headers).status_code == 400
