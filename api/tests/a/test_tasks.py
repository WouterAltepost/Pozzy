import uuid
from datetime import date, timedelta


def _create(client, headers, **overrides):
    body = {"title": "Write report", "urgent": True, "important": True}
    body.update(overrides)
    res = client.post("/api/tasks", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_tasks_require_auth(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "x"}).status_code == 401


def test_create_and_get_task(client, headers, areas):
    task = _create(client, headers, area_id=areas["Work"], tags=["UDefine", "UDefine", " "], due_date="2026-09-20", estimated_minutes=90)
    assert task["quadrant"] == "do"
    assert task["status"] == "todo"
    assert task["tags"] == ["UDefine"]
    assert task["area_id"] == areas["Work"]
    assert task["due_date"] == "2026-09-20"
    assert task["source"] == "manual"

    res = client.get(f"/api/tasks/{task['id']}", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["title"] == "Write report"


def test_create_validation(client, headers):
    assert client.post("/api/tasks", json={}, headers=headers).status_code == 400
    assert client.post("/api/tasks", json={"title": "  "}, headers=headers).status_code == 400
    assert client.post("/api/tasks", json={"title": "x", "status": "weird"}, headers=headers).status_code == 400
    assert client.post("/api/tasks", json={"title": "x", "due_date": "20-09-2026"}, headers=headers).status_code == 400
    assert client.post("/api/tasks", json={"title": "x", "tags": "a"}, headers=headers).status_code == 400
    res = client.post("/api/tasks", json={"title": "x", "area_id": str(uuid.uuid4())}, headers=headers)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"
    res = client.post(
        "/api/tasks",
        json={"title": "x", "scheduled_start": "2026-09-15T10:00:00+02:00", "scheduled_end": "2026-09-15T09:00:00+02:00"},
        headers=headers,
    )
    assert res.status_code == 400


def test_patch_and_quadrant(client, headers):
    task = _create(client, headers)
    res = client.patch(f"/api/tasks/{task['id']}", json={"quadrant": "schedule", "title": "Renamed"}, headers=headers)
    data = res.get_json()["data"]
    assert data["urgent"] is False and data["important"] is True and data["quadrant"] == "schedule"
    assert data["title"] == "Renamed"

    res = client.post(f"/api/tasks/{task['id']}/move", json={"quadrant": "eliminate"}, headers=headers)
    assert res.get_json()["data"]["quadrant"] == "eliminate"
    assert client.post(f"/api/tasks/{task['id']}/move", json={"quadrant": "nope"}, headers=headers).status_code == 400
    assert client.patch(f"/api/tasks/{task['id']}", json={}, headers=headers).status_code == 400


def test_done_sets_completed_at_and_back(client, headers):
    task = _create(client, headers)
    data = client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}, headers=headers).get_json()["data"]
    assert data["completed_at"] is not None
    data = client.patch(f"/api/tasks/{task['id']}", json={"status": "todo"}, headers=headers).get_json()["data"]
    assert data["completed_at"] is None


def test_complete_logs_hours(client, headers, areas):
    task = _create(client, headers, estimated_minutes=45, area_id=areas["Study"])
    res = client.post(f"/api/tasks/{task['id']}/complete", json={}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "done"

    from app.extensions import db
    from app.models import HoursLog

    logs = db.session.query(HoursLog).all()
    assert len(logs) == 1
    assert logs[0].minutes == 45
    assert str(logs[0].area_id) == areas["Study"]

    # Completing again with actual minutes updates the same log instead of duplicating it.
    client.post(f"/api/tasks/{task['id']}/complete", json={"actual_minutes": 60}, headers=headers)
    logs = db.session.query(HoursLog).all()
    assert len(logs) == 1 and logs[0].minutes == 60


def test_complete_without_minutes_logs_nothing(client, headers):
    task = _create(client, headers)
    client.post(f"/api/tasks/{task['id']}/complete", headers=headers)
    from app.extensions import db
    from app.models import HoursLog

    assert db.session.query(HoursLog).count() == 0


def test_list_filters(client, headers, areas):
    today = date.today()
    _create(client, headers, title="A", due_date=(today - timedelta(days=1)).isoformat())
    _create(client, headers, title="B", due_date=today.isoformat(), urgent=False, important=False)
    _create(client, headers, title="C", status="done")
    _create(client, headers, title="D", area_id=areas["Health"], status="inbox")

    data = client.get("/api/tasks", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["D", "A", "B"]  # inbox first, then by due date

    data = client.get("/api/tasks?include_closed=1", headers=headers).get_json()["data"]
    assert len(data) == 4

    data = client.get("/api/tasks?status=done", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["C"]

    data = client.get("/api/tasks?due=overdue", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["A"]

    data = client.get("/api/tasks?due=today_or_overdue", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["A", "B"]

    data = client.get("/api/tasks?quadrant=eliminate", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["B"]

    data = client.get(f"/api/tasks?area_id={areas['Health']}", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["D"]

    data = client.get("/api/tasks?q=a", headers=headers).get_json()["data"]
    assert [t["title"] for t in data] == ["A"]

    assert client.get("/api/tasks?quadrant=zzz", headers=headers).status_code == 400


def test_delete_task(client, headers):
    task = _create(client, headers)
    assert client.delete(f"/api/tasks/{task['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/tasks/{task['id']}", headers=headers).status_code == 404
    assert client.delete(f"/api/tasks/{task['id']}", headers=headers).status_code == 404
    assert client.get("/api/tasks/not-a-uuid", headers=headers).status_code == 404


def test_source_from_email(client, headers):
    task = _create(client, headers, source="email", source_ref=str(uuid.uuid4()))
    assert task["source"] == "email"
    assert task["source_ref"]
