"""Briefing replies: note stored, Claude rewrites the briefing and proposes actions, nothing applied
until the user picks. Ids outside the candidates are dropped; deterministic fallback keeps the note."""
import json
from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.models import AiCall, DailyBriefing, DailyDo, Note, Task
from app.modules.ai import briefing


def _task(client, headers, title):
    return client.post("/api/tasks", json={"title": title, "due_date": date.today().isoformat()}, headers=headers).get_json()["data"]["id"]


def test_note_rewrites_briefing_and_proposes_validated_actions(client, headers, fake_claude):
    task_id = _task(client, headers, "Fix Railway deploy")
    fake_claude.reply = json.dumps({"text": "Original briefing."})
    client.post("/api/ai/briefing", headers=headers)
    fake_claude.reply = json.dumps({
        "reply": "Good, the deploy is off your plate.",
        "text": "Updated briefing without the deploy.",
        "actions": [
            {"type": "complete_task", "task_id": task_id, "reason": "deploy fixed"},
            {"type": "complete_task", "task_id": "00000000-0000-0000-0000-000000000000", "reason": "invented"},
            {"type": "mark_email_handled", "email_id": "nope", "reason": "invented"},
            {"type": "add_do", "title": "Tell the team", "reason": "he said so"},
            {"type": "set_hour_target", "area": "Work", "hours": 0, "reason": "off this week"},
            {"type": "set_hour_target", "area": "Nonsense", "hours": 3},
            {"type": "explode", "reason": "not allowed"},
        ],
    })
    data = client.post("/api/ai/briefing/notes", json={"text": "The Railway deploy is fixed."}, headers=headers).get_json()["data"]
    assert data["text"] == "Updated briefing without the deploy." and data["source"] == "claude"
    assert len(data["notes"]) == 1
    note = data["notes"][0]
    assert note["text"] == "The Railway deploy is fixed." and note["reply"].startswith("Good")
    assert [a["type"] for a in note["actions"]] == ["complete_task", "add_do", "set_hour_target"]
    assert all(a["applied"] is False for a in note["actions"])
    assert note["actions"][0]["label"] == "Complete task: Fix Railway deploy"
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["note"] == "The Railway deploy is fixed." and sent["briefing"] == "Original briefing."
    assert sent["candidates"]["tasks"][0]["id"] == task_id and "Work" in sent["candidates"]["areas"]
    assert db.session.scalars(select(AiCall).where(AiCall.feature == "briefing_reply")).one()
    # Nothing was applied yet.
    assert db.session.get(Task, __import__("uuid").UUID(task_id)).status != "done"
    assert db.session.scalar(select(DailyDo)) is None


def test_apply_selected_actions_only_and_idempotent(client, headers, fake_claude):
    task_id = _task(client, headers, "Fix Railway deploy")
    fake_claude.reply = json.dumps({"text": "Original."})
    client.post("/api/ai/briefing", headers=headers)
    fake_claude.reply = json.dumps({
        "reply": "Ok.", "text": "Updated.",
        "actions": [
            {"type": "complete_task", "task_id": task_id, "reason": "done"},
            {"type": "add_do", "title": "Tell the team"},
            {"type": "add_note", "title": "Deploy fix", "body": "Railway EBUSY fixed by npm run build."},
            {"type": "set_hour_target", "area": "Work", "hours": 0, "reason": "off"},
        ],
    })
    client.post("/api/ai/briefing/notes", json={"text": "Deploy fixed, off this week."}, headers=headers)
    res = client.post("/api/ai/briefing/notes/0/apply", json={"actions": [0, 2, 3, 9]}, headers=headers).get_json()["data"]
    assert [r["index"] for r in res["results"]] == [0, 2, 3] and all(r["ok"] for r in res["results"])
    assert db.session.get(Task, __import__("uuid").UUID(task_id)).status == "done"
    assert db.session.scalar(select(DailyDo)) is None
    assert db.session.scalar(select(Note)).tags == ["briefing"]
    assert client.get("/api/settings", headers=headers).get_json()["data"]["hour_targets"]["Work"] == 0
    applied = [a["applied"] for a in res["briefing"]["notes"][0]["actions"]]
    assert applied == [True, False, True, True]
    again = client.post("/api/ai/briefing/notes/0/apply", json={"actions": [0, 1]}, headers=headers).get_json()["data"]
    assert again["results"][0]["message"] == "already applied" and again["results"][1]["ok"]
    assert db.session.scalar(select(DailyDo)).title == "Tell the team"


def test_apply_validates_input(client, headers, fake_claude):
    r = client.post("/api/ai/briefing/notes/0/apply", json={"actions": "x"}, headers=headers)
    assert r.status_code == 400 and r.get_json()["error"]["code"] == "validation_error"
    r = client.post("/api/ai/briefing/notes/0/apply", json={"actions": [0]}, headers=headers)
    assert r.status_code == 400
    r = client.post("/api/ai/briefing/notes", json={"text": ""}, headers=headers)
    assert r.status_code == 400
    r = client.post("/api/ai/briefing/notes", json={"text": "hi"})
    assert r.status_code == 401


def test_note_without_ai_keeps_note_and_no_proposals(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"briefing": False}}, headers=headers)
    data = client.post("/api/ai/briefing/notes", json={"text": "I am off this week."}, headers=headers).get_json()["data"]
    assert data["source"] == "deterministic" and "Your note: I am off this week." in data["text"]
    assert data["notes"][0]["actions"] == [] and data["notes"][0]["source"] == "deterministic"
    assert fake_claude.calls == []
    # Notes reach the next regeneration so Claude can honour them.
    client.put("/api/settings", json={"ai_enabled": {"briefing": True}}, headers=headers)
    fake_claude.reply = json.dumps({"text": "Quiet week then."})
    client.post("/api/ai/briefing", headers=headers)
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["notes"] == ["I am off this week."]
    row = db.session.scalar(select(DailyBriefing))
    assert len(row.notes_json) == 1


def test_validate_actions_caps_and_shapes():
    cands = {"emails": [{"id": "e1", "from": "Ace & Tate", "subject": "Order"}], "tasks": [], "areas": ["Work"]}
    out = briefing.validate_actions([{"type": "mark_email_handled", "email_id": "e1", "reason": "not mine"}] * 10, cands)
    assert len(out) == 6 and out[0]["label"] == "Mark handled: Ace & Tate, Order" and out[5]["index"] == 5
    assert briefing.validate_actions([{"type": "set_hour_target", "area": "Work", "hours": "lots"}], cands) == []
    assert briefing.validate_actions("garbage", cands) == []
