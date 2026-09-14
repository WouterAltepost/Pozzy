"""calendar_read / calendar_write as stream A calls them."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import CalendarEvent, Task
from app.services import calendar_read, calendar_write

from .conftest import CAL_A, CAL_B, NOW
from .test_sync import run_job


def _synced(app, fake_client):
    fake_client.put(CAL_A, "single.ics")  # 15 Sep 14:00-14:30 CEST
    fake_client.put(CAL_A, "allday.ics")  # 18 Sep all day
    fake_client.put(CAL_B, "weekly.ics")  # Mondays 10:00
    run_job(app)


def test_get_events_between_returns_utc_pairs_without_all_day(app, fake_client):
    _synced(app, fake_client)
    start = datetime(2026, 9, 14, tzinfo=timezone.utc)
    end = datetime(2026, 9, 21, tzinfo=timezone.utc)
    pairs = calendar_read.get_events_between(start, end)
    assert pairs == [
        (datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc), datetime(2026, 9, 14, 13, 0, tzinfo=timezone.utc)),  # moved standup
        (datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc), datetime(2026, 9, 15, 12, 30, tzinfo=timezone.utc)),
    ]
    assert all(p[0].tzinfo is not None for p in pairs)


def test_get_events_between_excludes_task_linked_events(app, fake_client):
    _synced(app, fake_client)
    task = Task(title="Report", status="scheduled")
    db.session.add(task)
    db.session.commit()
    row = db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == "single-1"))
    row.task_id = task.id
    db.session.commit()
    pairs = calendar_read.get_events_between(datetime(2026, 9, 15, tzinfo=timezone.utc), datetime(2026, 9, 16, tzinfo=timezone.utc))
    assert pairs == []


def test_get_events_between_accepts_local_tz_inputs(app, fake_client):
    from zoneinfo import ZoneInfo

    _synced(app, fake_client)
    ams = ZoneInfo("Europe/Amsterdam")
    pairs = calendar_read.get_events_between(datetime(2026, 9, 15, 13, 0, tzinfo=ams), datetime(2026, 9, 15, 15, 0, tzinfo=ams))
    assert len(pairs) == 1


def _scheduled_task(**kw):
    task = Task(title="Write report", description="Section 2", status="scheduled", estimated_minutes=90)
    task.scheduled_start = datetime(2026, 9, 16, 7, 0, tzinfo=timezone.utc)
    task.scheduled_end = datetime(2026, 9, 16, 8, 30, tzinfo=timezone.utc)
    for k, v in kw.items():
        setattr(task, k, v)
    db.session.add(task)
    db.session.commit()
    return task


def test_create_event_writes_icloud_and_mirrors_locally(app, fake_client):
    run_job(app)  # bootstraps the account and write calendar
    task = _scheduled_task()
    uid = calendar_write.create_event(task)
    task.calendar_uid = uid
    db.session.commit()

    assert uid and len(fake_client.created) == 1
    calendar_url, ics = fake_client.created[0]
    assert calendar_url == CAL_A
    assert f"X-POZZY-TASK-ID:{task.id}" in ics and f"UID:{uid}" in ics
    assert "SUMMARY:Write report" in ics and "DTSTART:20260916T070000Z" in ics
    row = db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == uid))
    assert row.task_id == task.id and row.calendar_url == CAL_A and row.title == "Write report"

    # The next sync sees the same event on the server and keeps exactly one row.
    run_job(app)
    assert db.session.scalar(select(db.func.count()).select_from(CalendarEvent)) == 1


def test_create_event_returns_none_without_account(app, monkeypatch):
    monkeypatch.setitem(app.config, "ICLOUD_USERNAME", None)
    task = _scheduled_task()
    assert calendar_write.create_event(task) is None


def test_create_event_fills_end_from_estimate(app, fake_client):
    run_job(app)
    task = _scheduled_task(scheduled_end=None, estimated_minutes=45)
    uid = calendar_write.create_event(task)
    row = db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == uid))
    assert row.end.replace(tzinfo=timezone.utc) - row.start.replace(tzinfo=timezone.utc) == timedelta(minutes=45)


def test_update_and_delete_round_trip(app, fake_client):
    run_job(app)
    task = _scheduled_task()
    task.calendar_uid = calendar_write.create_event(task)
    db.session.commit()

    task.scheduled_start += timedelta(days=1)
    task.scheduled_end += timedelta(days=1)
    task.title = "Write report v2"
    assert calendar_write.update_event(task) is True
    assert len(fake_client.updated) == 1
    _, uid, ics = fake_client.updated[0]
    assert uid == task.calendar_uid and "DTSTART:20260917T070000Z" in ics and "SUMMARY:Write report v2" in ics
    row = db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == uid))
    assert row.title == "Write report v2" and row.start.day == 17

    assert calendar_write.delete_event(task) is True
    assert fake_client.deleted == [(CAL_A, uid)]
    assert db.session.scalar(select(CalendarEvent).where(CalendarEvent.uid == uid)) is None
    assert fake_client.get_event(CAL_A, uid) is None


def test_update_recreates_when_deleted_on_phone(app, fake_client):
    run_job(app)
    task = _scheduled_task()
    task.calendar_uid = calendar_write.create_event(task)
    db.session.commit()
    fake_client.objects[CAL_A] = []  # gone from iCloud
    assert calendar_write.update_event(task) is True
    assert len(fake_client.created) == 2
    assert fake_client.get_event(CAL_A, task.calendar_uid) is not None


def test_update_without_uid_is_false(app, fake_client):
    run_job(app)
    task = _scheduled_task()
    assert calendar_write.update_event(task) is False
    assert calendar_write.delete_event(task) is False


def test_write_failure_propagates_so_a_keeps_local_schedule(app, fake_client):
    import pytest

    from app.integrations.caldav_client import CalDAVError

    run_job(app)
    fake_client.failing.add(CAL_A)
    task = _scheduled_task()
    with pytest.raises(CalDAVError):
        calendar_write.create_event(task)
    assert db.session.scalar(select(db.func.count()).select_from(CalendarEvent)) == 0


def test_stream_a_schedule_endpoint_creates_icloud_event(client, headers, app, fake_client):
    """End to end through A's route: no change in A, real write happens."""
    run_job(app)
    res = client.post("/api/tasks", json={"title": "Prep exam", "estimated_minutes": 60}, headers=headers)
    assert res.status_code == 201, res.get_json()
    task_id = res.get_json()["data"]["id"]
    res = client.post(f"/api/tasks/{task_id}/schedule", json={"start": "2026-09-17T09:00:00+02:00"}, headers=headers)
    assert res.status_code == 200, res.get_json()
    data = res.get_json()["data"]
    assert data["status"] == "scheduled" and data["calendar_uid"]
    assert len(fake_client.created) == 1 and f"X-POZZY-TASK-ID:{task_id}" in fake_client.created[0][1]
    agenda = client.get("/api/calendar/events?start=2026-09-17T00:00:00%2B02:00&end=2026-09-18T00:00:00%2B02:00", headers=headers).get_json()["data"]
    assert [e["task_id"] for e in agenda["events"]] == [task_id]
    assert [t["id"] for t in agenda["tasks"]] == [task_id]
