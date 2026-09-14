"""Sync job against the fake client. Nothing here touches the network."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.extensions import db
from app.integrations.caldav_client import build_ics
from app.jobs import calendar_sync
from app.models import CalendarAccount, CalendarEvent, JobRun, Task
from app.modules.calendar import service

from .conftest import CAL_A, CAL_B, NOW, load_ics


def rows(calendar_url=None):
    q = select(CalendarEvent).order_by(CalendarEvent.start, CalendarEvent.title)
    if calendar_url:
        q = q.where(CalendarEvent.calendar_url == calendar_url)
    return db.session.scalars(q).all()


def snapshot():
    return sorted((r.calendar_url, r.uid, r.recurrence_id, r.title, r.start.isoformat(), r.end.isoformat(), r.etag) for r in rows())


def run_job(app):
    calendar_sync.now_fn = lambda: NOW
    return calendar_sync.run(app)


def test_first_sync_bootstraps_account_and_selects_all_calendars(app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    msg = run_job(app)
    account = db.session.scalar(select(CalendarAccount))
    assert account.username == "wout@icloud.test"
    assert account.secret_ref == "ICLOUD_APP_PASSWORD"
    assert account.calendar_urls == [CAL_A, CAL_B]
    assert account.write_calendar_url == CAL_A
    assert [c["name"] for c in account.known_calendars] == ["Taken", "Uni"]
    assert account.last_synced_at is not None and account.last_sync_error is None
    assert "1 inserted" in msg
    job = db.session.scalar(select(JobRun).where(JobRun.name == "calendar_sync"))
    assert job.ok is True and job.message == msg


def test_sync_is_idempotent(app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    fake_client.put(CAL_A, "weekly.ics")
    fake_client.put(CAL_B, "allday.ics")
    fake_client.put(CAL_B, "dst.ics")
    first_msg = run_job(app)
    first = snapshot()
    # window 7 Sep to 14 Oct: single 1, weekly 5 (7,14,28 Sep, 5,12 Oct; 21 excluded), allday 1, dst none (starts 19 Oct)
    assert len(first) == 7, first_msg
    second_msg = run_job(app)
    assert snapshot() == first
    assert "inserted" not in second_msg and "7 unchanged" in second_msg
    assert db.session.scalar(select(db.func.count()).select_from(JobRun)) == 2


def test_sync_window_uses_settings_and_local_midnight(app, fake_client):
    start, end = service.sync_window(NOW)
    assert start == datetime(2026, 9, 6, 22, 0, tzinfo=timezone.utc)  # 7 Sep 00:00 CEST
    assert end == datetime(2026, 10, 13, 22, 0, tzinfo=timezone.utc)  # 14 Oct 00:00 CEST


def test_changed_etag_updates_and_vanished_event_is_deleted(app, fake_client):
    fake_client.put(CAL_A, "single.ics", etag="e1")
    fake_client.put(CAL_A, "allday.ics", etag="e2")
    run_job(app)
    assert [r.title for r in rows()] == ["Pillen bellen", "Deadline NGS"]

    renamed = load_ics("single.ics").replace("Pillen bellen", "Apotheek bellen")
    fake_client.put(CAL_A, renamed, etag="e1-changed", href=f"{CAL_A}single.ics")
    fake_client.remove(CAL_A, "allday.ics")
    msg = run_job(app)
    assert [r.title for r in rows()] == ["Apotheek bellen"]
    assert rows()[0].etag == "e1-changed"
    assert "1 updated" in msg and "1 deleted" in msg


def test_exdate_added_later_removes_that_occurrence(app, fake_client):
    fake_client.put(CAL_A, "weekly.ics", etag="w1")
    run_job(app)
    assert len(rows()) == 5
    with_more_exdates = load_ics("weekly.ics").replace(
        "EXDATE;TZID=Europe/Amsterdam:20260921T100000", "EXDATE;TZID=Europe/Amsterdam:20260921T100000,20260928T100000"
    )
    fake_client.put(CAL_A, with_more_exdates, etag="w2", href=f"{CAL_A}weekly.ics")
    msg = run_job(app)
    assert len(rows()) == 4
    assert "1 deleted" in msg


def test_one_calendar_failing_keeps_the_other_and_marks_job_failed(app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    fake_client.put(CAL_B, "allday.ics")
    run_job(app)
    assert len(rows()) == 2

    fake_client.failing.add(CAL_B)
    fake_client.remove(CAL_A, "single.ics")
    fake_client.put(CAL_A, "duration.ics")
    msg = run_job(app)
    # A was re-synced (single gone, duration in); B's rows untouched even though the fetch failed
    assert [r.uid for r in rows(CAL_A)] == ["duration-1"]
    assert [r.uid for r in rows(CAL_B)] == ["allday-1"]
    assert "failed: Uni" in msg
    job = db.session.scalars(select(JobRun).order_by(JobRun.started_at.desc())).first()
    assert job.ok is False and "503" in job.message
    account = db.session.scalar(select(CalendarAccount))
    assert "Uni" in account.last_sync_error
    assert account.last_synced_at is not None


def test_all_calendars_failing_is_a_job_failure(app, fake_client):
    fake_client.failing.update({CAL_A, CAL_B})
    msg = run_job(app)
    assert "all calendars failed" in msg
    job = db.session.scalar(select(JobRun))
    assert job.ok is False


def test_no_account_configured_is_a_clean_noop(app, monkeypatch):
    monkeypatch.setitem(app.config, "ICLOUD_USERNAME", None)
    msg = run_job(app)
    assert "no calendar account" in msg
    assert db.session.scalar(select(JobRun)).ok is True
    assert db.session.scalar(select(CalendarAccount)) is None


def test_deselected_calendar_rows_are_dropped(app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    fake_client.put(CAL_B, "allday.ics")
    run_job(app)
    account = db.session.scalar(select(CalendarAccount))
    service.update_account(account, {"calendar_urls": [CAL_A]})
    run_job(app)
    assert [r.calendar_url for r in rows()] == [CAL_A]
    assert fake_client.fetch_calls == 3  # 2 on the first run, 1 on the second


def test_pozzy_event_moved_on_phone_updates_task(app, fake_client):
    task = Task(title="Write report", status="scheduled", estimated_minutes=60)
    db.session.add(task)
    db.session.commit()
    start = datetime(2026, 9, 16, 7, 0, tzinfo=timezone.utc)
    end = datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)
    task.scheduled_start, task.scheduled_end = start, end
    uid, ics = build_ics(title="Write report", start=start, end=end, task_id=str(task.id))
    task.calendar_uid = uid
    db.session.commit()

    fake_client.put(CAL_A, ics, etag="p1", href=f"{CAL_A}{uid}.ics")
    run_job(app)
    [row] = rows()
    assert row.task_id == task.id

    # Moved two hours later on the iPhone
    moved = ics.replace("DTSTART:20260916T070000Z", "DTSTART:20260916T090000Z").replace("DTEND:20260916T080000Z", "DTEND:20260916T100000Z")
    fake_client.put(CAL_A, moved, etag="p2", href=f"{CAL_A}{uid}.ics")
    msg = run_job(app)
    db.session.refresh(task)
    assert task.scheduled_start.replace(tzinfo=timezone.utc) == datetime(2026, 9, 16, 9, 0, tzinfo=timezone.utc)
    assert task.scheduled_end.replace(tzinfo=timezone.utc) == datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc)
    assert "1 tasks_updated" in msg


def test_unparsable_object_is_skipped_not_fatal(app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    fake_client.put(CAL_A, "garbage", href=f"{CAL_A}broken.ics")
    msg = run_job(app)
    assert [r.uid for r in rows()] == ["single-1"]
    assert "1 skipped" in msg
    assert db.session.scalar(select(JobRun)).ok is True
