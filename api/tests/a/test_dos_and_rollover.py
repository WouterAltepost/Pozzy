from datetime import date, datetime, timezone

from app.extensions import db
from app.integrations import claude_client
from app.jobs import three_do_rollover
from app.models import DailyDo, JobRun


def _do(client, headers, **kw):
    body = {"title": "Read chapter 3", "date": "2026-09-14"}
    body.update(kw)
    res = client.post("/api/dos", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_dos_crud_and_positions(client, headers):
    a = _do(client, headers, title="A")
    b = _do(client, headers, title="B")
    assert (a["position"], b["position"]) == (1, 2)
    data = client.get("/api/dos?date=2026-09-14", headers=headers).get_json()["data"]
    assert [d["title"] for d in data] == ["A", "B"]
    assert client.get("/api/dos?date=2026-09-15", headers=headers).get_json()["data"] == []

    upd = client.patch(f"/api/dos/{a['id']}", json={"done": True, "position": 3}, headers=headers).get_json()["data"]
    assert upd["done"] is True and upd["position"] == 3
    assert client.patch(f"/api/dos/{a['id']}", json={}, headers=headers).status_code == 400
    assert client.delete(f"/api/dos/{a['id']}", headers=headers).status_code == 200
    assert client.delete(f"/api/dos/{a['id']}", headers=headers).status_code == 404
    assert client.post("/api/dos", json={"date": "2026-09-14"}, headers=headers).status_code == 400


def test_do_range_query(client, headers):
    _do(client, headers, date="2026-09-14")
    _do(client, headers, date="2026-09-15")
    _do(client, headers, date="2026-09-17")
    data = client.get("/api/dos?from=2026-09-14&to=2026-09-15", headers=headers).get_json()["data"]
    assert len(data) == 2
    assert client.get("/api/dos?from=2026-09-15&to=2026-09-14", headers=headers).status_code == 400


def test_do_linked_to_task_takes_title_and_syncs_done(client, headers):
    task = client.post("/api/tasks", json={"title": "Submit form", "estimated_minutes": 15}, headers=headers).get_json()["data"]
    do = _do(client, headers, title=None, task_id=task["id"])
    assert do["title"] == "Submit form"

    client.patch(f"/api/dos/{do['id']}", json={"done": True}, headers=headers)
    assert client.get(f"/api/tasks/{task['id']}", headers=headers).get_json()["data"]["status"] == "done"
    client.patch(f"/api/dos/{do['id']}", json={"done": False}, headers=headers)
    assert client.get(f"/api/tasks/{task['id']}", headers=headers).get_json()["data"]["status"] == "todo"


def _freeze(monkeypatch, iso_utc: str):
    frozen = datetime.fromisoformat(iso_utc).replace(tzinfo=timezone.utc)
    monkeypatch.setattr(three_do_rollover, "now_fn", lambda: frozen)


def test_rollover_across_midnight_with_frozen_clock(app, client, headers, monkeypatch):
    _do(client, headers, title="Finish essay", date="2026-09-14")
    done = _do(client, headers, title="Call dentist", date="2026-09-14")
    client.patch(f"/api/dos/{done['id']}", json={"done": True}, headers=headers)

    # 00:05 Amsterdam on the 15th is still 22:05 UTC on the 14th. Rollover must use the local date.
    _freeze(monkeypatch, "2026-09-14T22:05:00")
    message = three_do_rollover.run(app)
    assert "rolled 1 of 1" in message

    today = client.get("/api/dos?date=2026-09-15", headers=headers).get_json()["data"]
    assert [d["title"] for d in today] == ["Finish essay"]
    assert today[0]["rolled_from_date"] == "2026-09-14"
    assert today[0]["roll_count"] == 1 and today[0]["warning"] is False

    # Idempotent: running again copies nothing new.
    assert "rolled 0 of 1" in three_do_rollover.run(app)
    assert len(client.get("/api/dos?date=2026-09-15", headers=headers).get_json()["data"]) == 1

    # Second night: still undone, rolls again with the original date and a warning badge.
    _freeze(monkeypatch, "2026-09-15T22:05:00")
    three_do_rollover.run(app)
    day_after = client.get("/api/dos?date=2026-09-16", headers=headers).get_json()["data"]
    assert day_after[0]["rolled_from_date"] == "2026-09-14"
    assert day_after[0]["roll_count"] == 2 and day_after[0]["warning"] is True

    runs = db.session.query(JobRun).filter_by(name="three_do_rollover").all()
    assert len(runs) == 3 and all(r.ok for r in runs) and all(r.finished_at for r in runs)


def test_rollover_does_not_duplicate_manually_re_added_do(app, client, headers, monkeypatch):
    _do(client, headers, title="Gym", date="2026-09-14")
    _do(client, headers, title="gym ", date="2026-09-15")
    _freeze(monkeypatch, "2026-09-14T23:05:00")
    assert "rolled 0 of 1" in three_do_rollover.run(app)


def test_job_failure_is_logged_not_raised(app, monkeypatch):
    def boom(today):
        raise RuntimeError("db exploded")

    monkeypatch.setattr(three_do_rollover, "rollover_for", boom)
    message = three_do_rollover.run(app)
    assert "db exploded" in message
    run = db.session.query(JobRun).filter_by(name="three_do_rollover").one()
    assert run.ok is False and "db exploded" in run.message


def test_manual_rollover_endpoint(client, headers):
    res = client.post("/api/dos/rollover", headers=headers)
    assert res.status_code == 200 and "rolled" in res.get_json()["data"]["message"]


def test_suggest_dos_deterministic_and_claude_validation(client, headers, monkeypatch):
    overdue = client.post("/api/tasks", json={"title": "Pay rent", "due_date": "2026-09-10"}, headers=headers).get_json()["data"]
    urgent = client.post("/api/tasks", json={"title": "Fix bug", "urgent": True, "important": True}, headers=headers).get_json()["data"]
    client.post("/api/tasks", json={"title": "Someday", "urgent": False, "important": False}, headers=headers)
    _do(client, headers, title="Leftover", date="2026-09-14")

    data = client.post("/api/dos/suggest", json={"date": "2026-09-15"}, headers=headers).get_json()["data"]
    assert data["source"] == "deterministic"
    assert [s["title"] for s in data["suggestions"]] == ["Leftover", "Pay rent", "Fix bug"]
    assert data["suggestions"][1]["task_id"] == overdue["id"]

    def fake(candidates, context=None):
        return [
            {"title": "Fix bug", "task_id": urgent["id"], "reason": "blocking"},
            {"title": "Invented", "task_id": "not-a-real-id", "reason": "x"},
            {"title": "", "task_id": None},
        ]

    monkeypatch.setattr(claude_client, "suggest_dos", fake)
    data = client.post("/api/dos/suggest", json={"date": "2026-09-15"}, headers=headers).get_json()["data"]
    assert data["source"] == "claude"
    assert [(s["title"], s["task_id"]) for s in data["suggestions"]] == [("Fix bug", urgent["id"]), ("Invented", None)]


def test_suggest_dos_with_nothing_open(client, headers):
    data = client.post("/api/dos/suggest", json={}, headers=headers).get_json()["data"]
    assert data["suggestions"] == []
