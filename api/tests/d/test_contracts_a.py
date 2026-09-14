"""rank_slots and suggest_dos per docs/AI_CONTRACTS.md, through the fake client and through A's endpoints."""
import json

from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.models import AiCall

CANDS = [
    {"start": "2026-09-14T08:00:00+02:00", "end": "2026-09-14T09:30:00+02:00", "day_label": "Mon 14 Sep", "reason_hints": ["morning", "today"]},
    {"start": "2026-09-15T08:00:00+02:00", "end": "2026-09-15T09:30:00+02:00", "day_label": "Tue 15 Sep", "reason_hints": ["morning"]},
    {"start": "2026-09-15T14:00:00+02:00", "end": "2026-09-15T15:30:00+02:00", "day_label": "Tue 15 Sep", "reason_hints": ["afternoon"]},
]
TASK = {"title": "Deep work", "urgent": False, "important": True, "due_date": "2026-09-16", "estimated_minutes": 90}


def test_rank_slots_returns_only_known_slots_in_order(app, fake_claude):
    fake_claude.reply = json.dumps({"slots": [
        {"start": CANDS[2]["start"], "end": CANDS[2]["end"], "reason": "afternoon admin"},
        {"start": "2026-09-20T08:00:00+02:00", "end": "2026-09-20T09:30:00+02:00", "reason": "invented"},
        {"start": CANDS[0]["start"], "end": "2026-09-14T10:00:00+02:00", "reason": "shifted end"},
        {"start": CANDS[0]["start"], "end": CANDS[0]["end"], "reason": "morning"},
        {"start": CANDS[0]["start"], "end": CANDS[0]["end"], "reason": "duplicate"},
    ]})
    out = claude_client.rank_slots(TASK, CANDS, {"limit": 3})
    assert out == [
        {"start": CANDS[2]["start"], "end": CANDS[2]["end"], "reason": "afternoon admin"},
        {"start": CANDS[0]["start"], "end": CANDS[0]["end"], "reason": "morning"},
    ]
    sent = fake_claude.last_user_text()
    assert "Deep work" in sent and '"limit": 3' in sent
    assert fake_claude.last["model"] == app.config["CLAUDE_MODEL_SMART"]
    assert db.session.scalar(select(AiCall)).feature == "rank_slots"


def test_rank_slots_limit_and_empty(app, fake_claude):
    fake_claude.reply = json.dumps({"slots": [{"start": c["start"], "end": c["end"], "reason": "r"} for c in CANDS]})
    assert len(claude_client.rank_slots(TASK, CANDS, {"limit": 2})) == 2
    assert claude_client.rank_slots(TASK, [], {"limit": 3}) is None
    fake_claude.reply = json.dumps({"slots": []})
    assert claude_client.rank_slots(TASK, CANDS, None) is None


def test_rank_slots_bad_shape_is_none(app, fake_claude):
    fake_claude.reply = json.dumps([{"start": 1}])
    assert claude_client.rank_slots(TASK, CANDS, {"limit": 3}) is None


def test_rank_slots_kill_switch(app, fake_claude):
    from app.models import Setting

    row = db.session.scalar(select(Setting).where(Setting.key == "ai_enabled"))
    row.value = {**row.value, "scheduling": False}
    db.session.commit()
    assert claude_client.rank_slots(TASK, CANDS, {"limit": 3}) is None
    assert fake_claude.calls == []


def test_suggest_slot_endpoint_ranked_by_claude(client, headers, fake_claude):
    task = client.post("/api/tasks", json={"title": "Deep work", "important": True, "estimated_minutes": 90, "due_date": "2026-09-16"}, headers=headers).get_json()["data"]
    fake_claude.reply = json.dumps({"slots": [{"start": "2026-09-15T08:00:00+02:00", "end": "2026-09-15T09:30:00+02:00", "reason": "Fresh in the morning, a day before the due date."}]})
    data = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers).get_json()["data"]
    assert data["ranked_by"] == "claude"
    assert data["slots"][0]["start"] == "2026-09-15T08:00:00+02:00"
    assert data["slots"][0]["reason"].startswith("Fresh")
    payload = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert len(payload["candidates"]) <= 12 and payload["task"]["id"] == task["id"]


def test_suggest_slot_endpoint_falls_back_on_garbage(client, headers, fake_claude):
    task = client.post("/api/tasks", json={"title": "Deep work", "estimated_minutes": 60}, headers=headers).get_json()["data"]
    fake_claude.reply = "nope"
    data = client.post(f"/api/tasks/{task['id']}/suggest-slot", json={"from": "2026-09-14T06:00:00+02:00"}, headers=headers).get_json()["data"]
    assert data["ranked_by"] == "deterministic" and len(data["slots"]) == 3


DOS_CANDS = {
    "date": "2026-09-15",
    "tasks": [{"id": "t1", "title": "Fix bug", "quadrant": "do", "due_date": "2026-09-16", "area": "Work", "estimated_minutes": 60}],
    "deadlines": [{"id": "d1", "title": "Essay", "course": "Ethics", "due_at": "2026-09-18T23:59:00+02:00", "task_id": "t9"}],
    "weekly_goals": [],
    "rolled_over": [{"title": "Leftover", "rolled_from_date": "2026-09-14"}],
}


def test_suggest_dos_validates_ids_and_count(app, fake_claude):
    fake_claude.reply = json.dumps({"dos": [
        {"title": "Leftover", "task_id": None, "reason": "unfinished"},
        {"title": "Essay", "task_id": "t9", "reason": "deadline"},
        {"title": "  ", "task_id": "t1", "reason": "blank title dropped"},
        {"title": "Fix bug", "task_id": "made-up", "reason": "unknown id cleared"},
        {"title": "Fourth", "task_id": None, "reason": "over count"},
    ]})
    out = claude_client.suggest_dos(DOS_CANDS, {"count": 3})
    assert out == [
        {"title": "Leftover", "task_id": None, "reason": "unfinished"},
        {"title": "Essay", "task_id": "t9", "reason": "deadline"},
        {"title": "Fix bug", "task_id": None, "reason": "unknown id cleared"},
    ]
    assert '"count": 3' in fake_claude.last_user_text()
    assert db.session.scalar(select(AiCall)).feature == "suggest_dos"


def test_suggest_dos_failure_is_none(app, fake_claude):
    fake_claude.error = RuntimeError("down")
    assert claude_client.suggest_dos(DOS_CANDS, {"count": 3}) is None


def test_suggest_dos_endpoint_source_claude(client, headers, fake_claude):
    urgent = client.post("/api/tasks", json={"title": "Fix bug", "urgent": True, "important": True}, headers=headers).get_json()["data"]
    fake_claude.reply = json.dumps({"dos": [{"title": "Fix bug", "task_id": urgent["id"], "reason": "Urgent and important."}, {"title": "Walk", "task_id": None, "reason": "Health."}]})
    data = client.post("/api/dos/suggest", json={"date": "2026-09-15"}, headers=headers).get_json()["data"]
    assert data["source"] == "claude"
    assert [(s["title"], s["task_id"]) for s in data["suggestions"]] == [("Fix bug", urgent["id"]), ("Walk", None)]
