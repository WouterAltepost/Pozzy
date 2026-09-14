from datetime import date, datetime, timezone

from app.extensions import db
from app.jobs import deadline_urgency
from app.models import JobRun, Task
from app.utils import dates


def _course(client, headers, **kw):
    body = {"name": "Machine Learning", "code": "ML101", "period": "P1", "ects": 6}
    body.update(kw)
    res = client.post("/api/study/courses", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_course_crud(client, headers):
    c = _course(client, headers)
    assert c["status"] == "active"
    assert client.post("/api/study/courses", json={}, headers=headers).status_code == 400
    upd = client.patch(f"/api/study/courses/{c['id']}", json={"status": "passed"}, headers=headers).get_json()["data"]
    assert upd["status"] == "passed"
    assert client.get("/api/study/courses", headers=headers).get_json()["data"] == []
    assert len(client.get("/api/study/courses?include_closed=1", headers=headers).get_json()["data"]) == 1
    assert client.delete(f"/api/study/courses/{c['id']}", headers=headers).status_code == 200


def test_deadline_creates_linked_task_and_syncs(client, headers, areas, monkeypatch):
    today = date(2026, 9, 14)
    monkeypatch.setattr(dates, "today_local", lambda now=None: today)
    from app.modules.study import service

    monkeypatch.setattr(service, "today_local", lambda now=None: today)

    c = _course(client, headers)
    res = client.post("/api/study/deadlines", json={"course_id": c["id"], "title": "Assignment 1", "due_at": "2026-09-30T23:59:00+02:00", "type": "assignment"}, headers=headers)
    assert res.status_code == 201, res.get_json()
    d = res.get_json()["data"]
    assert d["task_id"] and d["course_code"] == "ML101"

    task = client.get(f"/api/tasks/{d['task_id']}", headers=headers).get_json()["data"]
    assert task["title"] == "Assignment 1 (ML101)"
    assert task["important"] is True and task["urgent"] is False
    assert task["due_date"] == "2026-09-30" and task["area_id"] == areas["Study"]
    assert task["tags"] == ["deadline", "ML101"] and task["source_ref"] == f"deadline:{d['id']}"

    # Due within 3 days: urgent immediately.
    soon = client.post("/api/study/deadlines", json={"course_id": c["id"], "title": "Quiz", "due_at": "2026-09-16T09:00:00+02:00"}, headers=headers).get_json()["data"]
    assert client.get(f"/api/tasks/{soon['task_id']}", headers=headers).get_json()["data"]["urgent"] is True

    # Edits propagate to the task.
    upd = client.patch(f"/api/study/deadlines/{d['id']}", json={"title": "Assignment 1b", "due_at": "2026-10-02T12:00:00+02:00"}, headers=headers).get_json()["data"]
    task = client.get(f"/api/tasks/{d['task_id']}", headers=headers).get_json()["data"]
    assert task["title"] == "Assignment 1b (ML101)" and task["due_date"] == "2026-10-02"

    # Done on the deadline closes the task; reopening reopens it.
    client.patch(f"/api/study/deadlines/{d['id']}", json={"done": True}, headers=headers)
    assert client.get(f"/api/tasks/{d['task_id']}", headers=headers).get_json()["data"]["status"] == "done"
    assert client.get("/api/study/deadlines", headers=headers).get_json()["data"][0]["id"] == soon["id"]
    assert len(client.get("/api/study/deadlines?include_done=1", headers=headers).get_json()["data"]) == 2
    client.patch(f"/api/study/deadlines/{d['id']}", json={"done": False}, headers=headers)
    assert client.get(f"/api/tasks/{d['task_id']}", headers=headers).get_json()["data"]["status"] == "todo"

    # Deleting an open deadline removes its auto-created task.
    client.delete(f"/api/study/deadlines/{soon['id']}", headers=headers)
    assert client.get(f"/api/tasks/{soon['task_id']}", headers=headers).status_code == 404

    # Deleting the course cascades deadlines and their open tasks.
    client.delete(f"/api/study/courses/{c['id']}", headers=headers)
    assert client.get(f"/api/tasks/{d['task_id']}", headers=headers).status_code == 404
    assert client.get("/api/study/deadlines?include_done=1", headers=headers).get_json()["data"] == []


def test_deadline_requires_valid_course(client, headers):
    res = client.post("/api/study/deadlines", json={"course_id": "00000000-0000-0000-0000-000000000000", "title": "x", "due_at": "2026-09-30T23:59:00+02:00"}, headers=headers)
    assert res.status_code == 400


def test_applications_kanban_and_upcoming(client, headers, monkeypatch):
    today = date(2026, 9, 14)
    monkeypatch.setattr(dates, "today_local", lambda now=None: today)
    from app.modules.study import service

    monkeypatch.setattr(service, "today_local", lambda now=None: today)

    a = client.post("/api/study/applications", json={"company": "Acme", "role": "ML intern", "link": "https://acme.example"}, headers=headers).get_json()["data"]
    assert a["status"] == "found" and a["applied_at"] is None
    a = client.patch(f"/api/study/applications/{a['id']}", json={"status": "applied", "next_step": "Follow up", "next_step_date": "2026-09-20"}, headers=headers).get_json()["data"]
    assert a["applied_at"] == "2026-09-14"
    far = client.post("/api/study/applications", json={"company": "Far", "status": "interview", "next_step_date": "2026-12-01"}, headers=headers).get_json()["data"]
    assert client.post("/api/study/applications", json={"company": "x", "status": "hired"}, headers=headers).status_code == 400

    c = _course(client, headers)
    client.post("/api/study/deadlines", json={"course_id": c["id"], "title": "Soon", "due_at": "2026-09-20T23:59:00+02:00"}, headers=headers)
    client.post("/api/study/deadlines", json={"course_id": c["id"], "title": "Later", "due_at": "2026-11-20T23:59:00+02:00"}, headers=headers)

    up = client.get("/api/study/upcoming?days=14", headers=headers).get_json()["data"]
    assert [d["title"] for d in up["deadlines"]] == ["Soon"]
    assert [s["company"] for s in up["application_steps"]] == ["Acme"]

    assert len(client.get("/api/study/applications", headers=headers).get_json()["data"]) == 2
    assert client.delete(f"/api/study/applications/{far['id']}", headers=headers).status_code == 200


def test_deadline_urgency_job(app, client, headers, monkeypatch):
    monkeypatch.setattr(deadline_urgency, "now_fn", lambda: datetime(2026, 9, 14, 6, 0, tzinfo=timezone.utc))
    soon = client.post("/api/tasks", json={"title": "Soon", "due_date": "2026-09-16"}, headers=headers).get_json()["data"]
    later = client.post("/api/tasks", json={"title": "Later", "due_date": "2026-09-25"}, headers=headers).get_json()["data"]
    done = client.post("/api/tasks", json={"title": "Done", "due_date": "2026-09-15", "status": "done"}, headers=headers).get_json()["data"]

    assert deadline_urgency.run(app) == "flipped urgent on 1 task(s)"
    assert db.session.get(Task, __import__("uuid").UUID(soon["id"])).urgent is True
    assert db.session.get(Task, __import__("uuid").UUID(later["id"])).urgent is False
    assert db.session.get(Task, __import__("uuid").UUID(done["id"])).urgent is False
    assert deadline_urgency.run(app) == "flipped urgent on 0 task(s)"
    assert db.session.query(JobRun).filter_by(name="deadline_urgency", ok=True).count() == 2


def test_settings_merge_defaults_and_job_runs(app, client, headers):
    data = client.get("/api/settings", headers=headers).get_json()["data"]
    assert data["deadline_urgent_days"] == 3 and data["briefing_time"] == "07:00"  # defaults, never seeded
    assert data["timezone"] == "Europe/Amsterdam"  # seeded
    deadline_urgency.run(app)
    runs = client.get("/api/settings/job-runs", headers=headers).get_json()["data"]
    assert runs[0]["name"] == "deadline_urgency" and runs[0]["ok"] is True and runs[0]["finished_at"]
    assert client.get("/api/settings/defaults", headers=headers).get_json()["data"]["three_dos_count"] == 3
