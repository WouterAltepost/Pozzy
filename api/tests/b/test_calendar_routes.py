from sqlalchemy import select

from app.extensions import db
from app.models import CalendarEvent, JobRun

from .conftest import CAL_A, CAL_B
from .test_sync import run_job

RANGE = "start=2026-09-14T00:00:00%2B02:00&end=2026-09-21T00:00:00%2B02:00"


def test_routes_require_auth(client):
    assert client.get("/api/calendar/events").status_code == 401
    assert client.post("/api/calendar/sync").status_code == 401
    assert client.get("/api/calendar/account").status_code == 401


def test_list_events_defaults_and_validation(client, headers):
    res = client.get("/api/calendar/events", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["events"] == [] and data["tasks"] == [] and data["start"] < data["end"]
    assert client.get("/api/calendar/events?start=nope", headers=headers).status_code == 400
    assert client.get("/api/calendar/events?start=2026-09-14T00:00:00%2B02:00&end=2026-09-13T00:00:00%2B02:00", headers=headers).status_code == 400


def test_list_events_in_range_are_local_iso(client, headers, app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    fake_client.put(CAL_B, "weekly.ics")
    run_job(app)
    data = client.get(f"/api/calendar/events?{RANGE}", headers=headers).get_json()["data"]
    titles = [(e["title"], e["start"]) for e in data["events"]]
    assert titles == [("Standup (moved)", "2026-09-14T14:00:00+02:00"), ("Pillen bellen", "2026-09-15T14:00:00+02:00")]
    assert data["events"][0]["recurrence_id"] and data["events"][1]["recurrence_id"] is None


def test_sync_endpoint_runs_and_reports(client, headers, app, fake_client):
    fake_client.put(CAL_A, "single.ics")
    res = client.post("/api/calendar/sync", headers=headers)
    assert res.status_code == 200, res.get_json()
    data = res.get_json()["data"]
    assert data["ok"] is True and "1 inserted" in data["message"]
    assert data["account"]["last_synced_at"] and data["account"]["last_sync_error"] is None
    assert db.session.scalar(select(db.func.count()).select_from(JobRun)) == 0  # manual sync is not a job run

    fake_client.failing.add(CAL_B)
    data = client.post("/api/calendar/sync", headers=headers).get_json()["data"]
    assert data["ok"] is False and "Uni" in data["message"]

    fake_client.failing.add(CAL_A)
    res = client.post("/api/calendar/sync", headers=headers)
    assert res.status_code == 502 and res.get_json()["error"]["code"] == "caldav_error"


def test_sync_without_account_is_ok(client, headers, app, monkeypatch):
    monkeypatch.setitem(app.config, "ICLOUD_USERNAME", None)
    data = client.post("/api/calendar/sync", headers=headers).get_json()["data"]
    assert data["ok"] is True and "no calendar account" in data["message"] and data["account"] is None


def test_account_get_put_discover(client, headers, app, fake_client):
    assert client.get("/api/calendar/account", headers=headers).get_json()["data"]["calendar_urls"] == []
    res = client.post("/api/calendar/account/discover", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert [c["name"] for c in data["calendars"]] == ["Taken", "Uni"]
    assert data["account"]["calendar_urls"] == [CAL_A, CAL_B] and data["account"]["write_calendar_url"] == CAL_A

    res = client.put("/api/calendar/account", json={"calendar_urls": [CAL_B], "write_calendar_url": CAL_B}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["calendar_urls"] == [CAL_B]
    assert client.put("/api/calendar/account", json={"calendar_urls": "x"}, headers=headers).status_code == 400
    assert client.put("/api/calendar/account", json={}, headers=headers).status_code == 400
    # Discovery again does not reset the selection
    client.post("/api/calendar/account/discover", headers=headers)
    assert client.get("/api/calendar/account", headers=headers).get_json()["data"]["calendar_urls"] == [CAL_B]


def test_event_crud_round_trip(client, headers, app, fake_client):
    run_job(app)
    body = {"title": "Dentist", "start": "2026-09-16T09:00:00+02:00", "end": "2026-09-16T09:30:00+02:00", "location": "Centrum"}
    res = client.post("/api/calendar/events", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    ev = res.get_json()["data"]
    assert ev["title"] == "Dentist" and ev["start"] == "2026-09-16T09:00:00+02:00" and ev["calendar_url"] == CAL_A
    assert len(fake_client.created) == 1 and "LOCATION:Centrum" in fake_client.created[0][1]

    res = client.put(f"/api/calendar/events/{ev['id']}", json={"title": "Dentist (moved)", "start": "2026-09-16T10:00:00+02:00", "end": "2026-09-16T10:30:00+02:00"}, headers=headers)
    assert res.status_code == 200, res.get_json()
    upd = res.get_json()["data"]
    assert upd["title"] == "Dentist (moved)" and upd["start"] == "2026-09-16T10:00:00+02:00" and upd["location"] == "Centrum"
    assert fake_client.updated[0][1] == ev["uid"]

    # Survives a sync: the fake server now holds the updated ICS
    run_job(app)
    listed = client.get(f"/api/calendar/events?{RANGE}", headers=headers).get_json()["data"]["events"]
    assert [e["title"] for e in listed] == ["Dentist (moved)"]

    assert client.delete(f"/api/calendar/events/{ev['id']}", headers=headers).status_code == 200
    assert fake_client.deleted == [(CAL_A, ev["uid"])]
    assert client.delete(f"/api/calendar/events/{ev['id']}", headers=headers).status_code == 404
    assert client.get(f"/api/calendar/events?{RANGE}", headers=headers).get_json()["data"]["events"] == []


def test_create_all_day_event(client, headers, app, fake_client):
    run_job(app)
    body = {"title": "Day off", "start": "2026-09-16T00:00:00+02:00", "end": "2026-09-16T00:00:00+02:00", "all_day": True}
    res = client.post("/api/calendar/events", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    ev = res.get_json()["data"]
    assert ev["all_day"] is True and ev["start"] == "2026-09-16T00:00:00+02:00" and ev["end"] == "2026-09-17T00:00:00+02:00"
    assert "DTSTART;VALUE=DATE:20260916" in fake_client.created[0][1]


def test_create_event_validation_and_config_errors(client, headers, app, fake_client, monkeypatch):
    run_job(app)
    assert client.post("/api/calendar/events", json={"title": ""}, headers=headers).status_code == 400
    assert client.post("/api/calendar/events", json={"title": "x", "start": "2026-09-16T10:00:00+02:00", "end": "2026-09-16T09:00:00+02:00"}, headers=headers).status_code == 400
    fake_client.failing.add(CAL_A)
    res = client.post("/api/calendar/events", json={"title": "x", "start": "2026-09-16T09:00:00+02:00", "end": "2026-09-16T10:00:00+02:00"}, headers=headers)
    assert res.status_code == 502 and res.get_json()["error"]["code"] == "caldav_error"
    assert db.session.scalar(select(db.func.count()).select_from(CalendarEvent)) == 0


def test_create_event_without_account_is_409(client, headers, app, monkeypatch):
    monkeypatch.setitem(app.config, "ICLOUD_USERNAME", None)
    res = client.post("/api/calendar/events", json={"title": "x", "start": "2026-09-16T09:00:00+02:00", "end": "2026-09-16T10:00:00+02:00"}, headers=headers)
    assert res.status_code == 409 and res.get_json()["error"]["code"] == "calendar_not_configured"


def test_recurring_occurrence_is_read_only(client, headers, app, fake_client):
    fake_client.put(CAL_B, "weekly.ics")
    run_job(app)
    occ = client.get(f"/api/calendar/events?{RANGE}", headers=headers).get_json()["data"]["events"][0]
    assert occ["recurrence_id"]
    res = client.put(f"/api/calendar/events/{occ['id']}", json={"title": "nope"}, headers=headers)
    assert res.status_code == 409 and res.get_json()["error"]["code"] == "recurring_not_editable"
    assert client.delete(f"/api/calendar/events/{occ['id']}", headers=headers).status_code == 409
    assert fake_client.updated == [] and fake_client.deleted == []


def test_deleting_task_event_clears_task_uid(client, headers, app, fake_client):
    run_job(app)
    task_id = client.post("/api/tasks", json={"title": "Prep", "estimated_minutes": 30}, headers=headers).get_json()["data"]["id"]
    client.post(f"/api/tasks/{task_id}/schedule", json={"start": "2026-09-17T09:00:00+02:00"}, headers=headers)
    ev = client.get("/api/calendar/events?start=2026-09-17T00:00:00%2B02:00&end=2026-09-18T00:00:00%2B02:00", headers=headers).get_json()["data"]["events"][0]
    assert ev["task_id"] == task_id
    client.delete(f"/api/calendar/events/{ev['id']}", headers=headers)
    task = client.get(f"/api/tasks/{task_id}", headers=headers).get_json()["data"]
    assert task["calendar_uid"] is None and task["status"] == "scheduled"
