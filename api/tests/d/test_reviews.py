"""review_stats snapshot, weekly review generation (Claude and fallback), edit, finalize, job."""
import json
from datetime import date, timedelta

from sqlalchemy import select

from app.extensions import db
from app.jobs import weekly_review_draft as job
from app.models import JobRun, WeeklyReview
from app.services import review_stats
from app.utils.dates import week_start_of

WEEK = week_start_of(date.today())


def _seed(client, headers, areas):
    d0 = WEEK.isoformat()
    done = client.post("/api/tasks", json={"title": "Done task", "area_id": areas["Work"]}, headers=headers).get_json()["data"]
    client.post(f"/api/tasks/{done['id']}/complete", json={}, headers=headers)
    client.post("/api/tasks", json={"title": "Urgent open", "urgent": True, "important": True, "due_date": d0}, headers=headers)
    client.post("/api/tasks", json={"title": "Someday", "important": True}, headers=headers)
    g1 = client.post("/api/goals", json={"title": "Goal hit", "week_start": d0}, headers=headers).get_json()["data"]
    client.patch(f"/api/goals/{g1['id']}", json={"done": True}, headers=headers)
    client.post("/api/goals", json={"title": "Goal missed", "week_start": d0, "area_id": areas["Study"]}, headers=headers)
    do1 = client.post("/api/dos", json={"date": d0, "title": "Do one"}, headers=headers).get_json()["data"]
    client.patch(f"/api/dos/{do1['id']}", json={"done": True}, headers=headers)
    client.post("/api/dos", json={"date": (WEEK + timedelta(days=1)).isoformat(), "title": "Do two"}, headers=headers)
    client.post("/api/hours", json={"date": d0, "minutes": 120, "area_id": areas["Work"]}, headers=headers)
    tr = client.post("/api/trackers", json={"name": "Creatine", "type": "daily_bool"}, headers=headers).get_json()["data"]
    client.post(f"/api/trackers/{tr['id']}/tick", json={"date": d0}, headers=headers)
    course = client.post("/api/study/courses", json={"name": "Ethics", "period": "P1", "ects": 5}, headers=headers).get_json()["data"]
    due = (WEEK + timedelta(days=9)).isoformat() + "T23:59:00+02:00"
    client.post("/api/study/deadlines", json={"course_id": course["id"], "title": "Essay", "due_at": due}, headers=headers)


def test_compute_snapshot(client, headers, areas):
    _seed(client, headers, areas)
    s = review_stats.compute(WEEK)
    assert s["week_start"] == WEEK.isoformat()
    assert s["goals"]["total"] == 2 and s["goals"]["done"] == 1
    assert sorted(s["goals"]["items"], key=lambda g: g["title"]) == [{"title": "Goal hit", "area": None, "done": True, "progress": None}, {"title": "Goal missed", "area": "Study", "done": False, "progress": None}]
    assert s["dos"]["total"] == 2 and s["dos"]["done"] == 1 and s["dos"]["rate"] == 0.5 and s["dos"]["missed"] == ["Do two"]
    assert s["tasks"]["done"] == 1 and s["tasks"]["done_titles"] == ["Done task"] and s["tasks"]["done_by_area"] == {"Work": 1}
    assert s["tasks"]["open"] == 3 and s["tasks"]["overdue"] == 1  # Urgent open + Someday + the Essay deadline task
    assert s["hours"]["total_hours"] == 2.0 and any(a["area"] == "Work" and a["hours"] == 2.0 and a["target_hours"] == 16.0 for a in s["hours"]["areas"])
    assert s["trackers"][0]["name"] == "Creatine" and s["trackers"][0]["week_total"] == 1
    assert s["deadlines"]["upcoming"][0]["title"] == "Essay" and s["deadlines"]["upcoming"][0]["task_id"]
    assert s["emails"] is None
    assert [c["title"] for c in s["open_task_candidates"]][:1] == ["Urgent open"]


def test_generate_with_claude_and_focus_validation(client, headers, areas, fake_claude):
    _seed(client, headers, areas)
    stats = review_stats.compute(WEEK)
    urgent_id = next(c["id"] for c in stats["open_task_candidates"] if c["title"] == "Urgent open")
    fake_claude.reply = json.dumps({"reflection": "Solid week.", "next_week_focus": [
        {"title": "Finish Urgent open", "area": "Work", "task_id": urgent_id, "reason": "due"},
        {"title": "Invented link", "task_id": "not-a-candidate", "reason": "x"},
        {"title": "", "reason": "dropped"},
    ]})
    data = client.post(f"/api/reviews/{WEEK.isoformat()}/generate", headers=headers).get_json()["data"]
    assert data["reflection"] == "Solid week." and data["reflection_source"] == "claude"
    assert [f["task_id"] for f in data["next_week_focus"]] == [urgent_id, None]
    assert data["stats"]["goals"]["done"] == 1
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["max_goals"] == 5 and sent["goals"]["total"] == 2
    assert client.get("/api/reviews/current", headers=headers).get_json()["data"]["id"] == data["id"]
    assert client.get("/api/reviews", headers=headers).get_json()["data"][0]["id"] == data["id"]


def test_generate_fallback_and_finalize_creates_goals(client, headers, areas, fake_claude):
    _seed(client, headers, areas)
    fake_claude.reply = "not json"
    data = client.post(f"/api/reviews/{WEEK.isoformat()}/generate", headers=headers).get_json()["data"]
    assert data["reflection_source"] == "deterministic" and "1 of 2 weekly goals done" in data["reflection"]
    titles = [f["title"] for f in data["next_week_focus"]]
    assert titles[:3] == ["Goal missed", "Essay", "Urgent open"] and "Someday" in titles

    data = client.patch(f"/api/reviews/{WEEK.isoformat()}", json={"notes": "Tired week.", "next_week_focus": [{"title": "Ship stream D", "area": "Work", "target_value": "1"}, {"title": "Essay", "area": "Study"}]}, headers=headers).get_json()["data"]
    assert data["notes"] == "Tired week." and data["next_week_focus"][0]["target_value"] == 1.0
    assert client.patch(f"/api/reviews/{WEEK.isoformat()}", json={"next_week_focus": [{"nope": 1}]}, headers=headers).status_code == 400

    out = client.post(f"/api/reviews/{WEEK.isoformat()}/finalize", headers=headers).get_json()["data"]
    assert out["review"]["finalized"] and [g["title"] for g in out["created_goals"]] == ["Ship stream D", "Essay"]
    next_week = (WEEK + timedelta(days=7)).isoformat()
    goals = client.get(f"/api/goals?week_start={next_week}", headers=headers).get_json()["data"]["goals"]
    assert {g["title"] for g in goals} == {"Ship stream D", "Essay"}
    assert next(g for g in goals if g["title"] == "Ship stream D")["area_id"] == areas["Work"]
    # finalized reviews are locked
    assert client.post(f"/api/reviews/{WEEK.isoformat()}/finalize", headers=headers).status_code == 400
    assert client.patch(f"/api/reviews/{WEEK.isoformat()}", json={"notes": "x"}, headers=headers).status_code == 400
    assert client.post(f"/api/reviews/{WEEK.isoformat()}/generate", headers=headers).status_code == 400


def test_kill_switch_off(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"weekly_review": False}}, headers=headers)
    data = client.post("/api/reviews/current/generate", headers=headers).get_json()["data"]
    assert data["reflection_source"] == "deterministic" and fake_claude.calls == []
    assert client.get("/api/reviews/2020-01-06", headers=headers).get_json()["data"] is None
    assert client.get("/api/reviews/bad", headers=headers).status_code == 400
    assert client.get("/api/reviews").status_code == 401


def test_job_idempotent(app, fake_claude):
    fake_claude.reply = json.dumps({"reflection": "Fine.", "next_week_focus": []})
    assert "drafted (claude)" in job.run(app)
    assert "already drafted" in job.run(app)
    assert len(fake_claude.calls) == 1
    assert db.session.scalar(select(db.func.count()).select_from(WeeklyReview)) == 1
    assert all(r.ok for r in db.session.scalars(select(JobRun).where(JobRun.name == "weekly_review_draft")).all())
