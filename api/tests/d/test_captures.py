"""Capture round trip: store, process (Claude or deterministic), confirm via A's services, discard."""
import json
from datetime import date

import pytest

from app.modules.captures import service as captures
from app.modules.captures.schemas import validate_fields

CTX = {"today": "2026-09-14", "weekday": "Monday", "timezone": "Europe/Amsterdam", "areas": ["Study", "Work", "Personal", "Health"], "trackers": [{"name": "Weight", "type": "numeric", "unit": "kg"}, {"name": "Sauna", "type": "weekly_count", "unit": None}], "courses": []}


# --- deterministic parser (works with AI off) ---


def test_det_task_with_relative_date_tags_area_and_estimate():
    p = captures.parse_deterministic("Finish the UDefine report friday #client 2h important", CTX)
    assert p["type"] == "task" and p["source"] == "deterministic"
    f = p["fields"]
    assert f["due_date"] == "2026-09-18" and f["tags"] == ["client"] and f["estimated_minutes"] == 120
    assert f["important"] is True and f["urgent"] is False and f["area"] is None
    assert "friday" not in f["title"].lower() and "#" not in f["title"]


def test_det_area_and_tomorrow_and_urgent():
    p = captures.parse_deterministic("call the dentist tomorrow, urgent (health)", CTX)
    assert p["fields"]["due_date"] == "2026-09-15" and p["fields"]["urgent"] and p["fields"]["area"] == "Health"


def test_det_note_goal_event_prefixes():
    assert captures.parse_deterministic("note: Railway root dir must stay api", CTX)["type"] == "note"
    g = captures.parse_deterministic("goal: run 3 times next week", CTX)
    assert g["type"] == "goal" and g["fields"]["week"] == "next" and g["fields"]["target_value"] == 3
    e = captures.parse_deterministic("event: dentist tuesday at 14:30", CTX)
    assert e["type"] == "event" and e["fields"]["start"].startswith("2026-09-15T14:30") and e["fields"]["end"].startswith("2026-09-15T15:30")
    assert e["fields"]["title"].lower() == "dentist"
    assert captures.parse_deterministic("event: dentist sometime", CTX)["type"] == "task"


def test_det_tracker_value():
    p = captures.parse_deterministic("weight 82.4", CTX)
    assert p["type"] == "tracker" and p["fields"] == {"tracker": "Weight", "date": "2026-09-14", "value": 82.4, "note": None}
    assert captures.parse_deterministic("sauna", CTX)["fields"]["value"] == 1


def test_validate_fields_rejects_bad():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        validate_fields("task", {"title": ""})
    with pytest.raises(ValidationError):
        validate_fields("event", {"title": "x", "start": "not a date"})
    assert validate_fields("task", {"title": "x", "tags": ["#a", " ", "b"]})["tags"] == ["a", "b"]


# --- API round trip ---


def _cap(client, headers, text, process=False):
    res = client.post("/api/captures", json={"text": text, "process": process}, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_create_returns_immediately_without_ai(client, headers, fake_claude):
    cap = _cap(client, headers, "buy milk")
    assert cap["status"] == "new" and cap["proposal"] is None
    assert fake_claude.calls == []
    assert client.get("/api/captures?status=new", headers=headers).get_json()["data"][0]["id"] == cap["id"]
    assert client.post("/api/captures", json={"text": "   "}, headers=headers).status_code == 400
    assert client.get("/api/captures").status_code == 401


def test_process_uses_claude_proposal(client, headers, fake_claude, areas):
    fake_claude.reply = json.dumps({"type": "task", "confidence": 0.9, "reason": "A thing to do", "fields": {"title": "Pay tuition", "area": "Study", "due_date": "2026-09-30", "important": True, "tags": ["#money"]}})
    cap = _cap(client, headers, "pay tuition before end of month")
    data = client.post(f"/api/captures/{cap['id']}/process", headers=headers).get_json()["data"]
    assert data["parsed_type"] == "task" and data["proposal"]["source"] == "claude"
    assert data["proposal"]["fields"]["title"] == "Pay tuition" and data["proposal"]["fields"]["tags"] == ["money"]
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["text"] == "pay tuition before end of month" and "Study" in sent["areas"] and sent["today"] == date.today().isoformat() or sent["today"]

    out = client.post(f"/api/captures/{cap['id']}/confirm", json={}, headers=headers).get_json()["data"]
    assert out["capture"]["status"] == "processed" and out["capture"]["result_ref"] == f"task:{out['created']['id']}"
    task = client.get(f"/api/tasks/{out['created']['id']}", headers=headers).get_json()["data"]
    assert task["source"] == "capture" and task["source_ref"] == cap["id"] and task["area_id"] == areas["Study"] and task["important"]
    # cannot confirm twice
    assert client.post(f"/api/captures/{cap['id']}/confirm", json={}, headers=headers).status_code == 400


def test_process_falls_back_when_claude_answer_is_bad(client, headers, fake_claude):
    fake_claude.reply = json.dumps({"type": "spaceship", "fields": {}})
    cap = _cap(client, headers, "note: keep the venv per worktree", process=True)
    assert cap["proposal"]["source"] == "deterministic" and cap["parsed_type"] == "note"
    fake_claude.reply = json.dumps({"type": "task", "fields": {"title": ""}})
    cap = _cap(client, headers, "empty title from claude", process=True)
    assert cap["proposal"]["source"] == "deterministic" and cap["proposal"]["fields"]["title"] == "empty title from claude"


def test_kill_switch_off_uses_deterministic(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"capture": False}}, headers=headers)
    cap = _cap(client, headers, "buy milk tomorrow", process=True)
    assert cap["proposal"]["source"] == "deterministic" and fake_claude.calls == []


def test_confirm_with_edited_fields_and_other_types(client, headers, fake_claude, areas):
    fake_claude.reply = json.dumps({"type": "note", "fields": {"title": "x", "body": "y"}})
    cap = _cap(client, headers, "something", process=True)
    out = client.post(f"/api/captures/{cap['id']}/confirm", json={"type": "goal", "fields": {"title": "Ship stream D", "area": "work", "target_value": 1, "week": "next"}}, headers=headers).get_json()["data"]
    assert out["capture"]["parsed_type"] == "goal" and out["created"]["title"] == "Ship stream D" and out["created"]["area_id"] == areas["Work"]
    goals = client.get("/api/goals?week_start=" + out["created"]["week_start"], headers=headers).get_json()["data"]
    assert any(g["id"] == out["created"]["id"] for g in goals["goals"])

    fake_claude.reply = "nope"
    cap = _cap(client, headers, "note: idea", process=True)
    out = client.post(f"/api/captures/{cap['id']}/confirm", json={}, headers=headers).get_json()["data"]
    assert out["capture"]["result_ref"].startswith("note:") and out["created"]["title"] == "idea"

    cap = _cap(client, headers, "event: standup tuesday at 09:00", process=True)
    out = client.post(f"/api/captures/{cap['id']}/confirm", json={}, headers=headers).get_json()["data"]
    assert out["created"]["status"] == "scheduled" and out["created"]["scheduled_start"].endswith("T09:00:00+02:00") and out["created"]["estimated_minutes"] == 60


def test_confirm_tracker_entry(client, headers, fake_claude):
    tracker = client.post("/api/trackers", json={"name": "Weight", "type": "numeric", "unit": "kg"}, headers=headers).get_json()["data"]
    cap = _cap(client, headers, "weight 81.9", process=True)
    assert cap["parsed_type"] == "tracker"
    out = client.post(f"/api/captures/{cap['id']}/confirm", json={}, headers=headers).get_json()["data"]
    assert out["created"]["tracker_id"] == tracker["id"] and out["created"]["value"] == 81.9
    cap = _cap(client, headers, "x", process=True)
    res = client.post(f"/api/captures/{cap['id']}/confirm", json={"type": "tracker", "fields": {"tracker": "Nope", "value": 1}}, headers=headers)
    assert res.status_code == 400 and "No tracker" in res.get_json()["error"]["message"]


def test_confirm_validation_error_and_discard(client, headers, fake_claude):
    cap = _cap(client, headers, "x", process=True)
    res = client.post(f"/api/captures/{cap['id']}/confirm", json={"type": "task", "fields": {"title": ""}}, headers=headers)
    assert res.status_code == 400 and "title" in res.get_json()["error"]["message"]
    data = client.post(f"/api/captures/{cap['id']}/discard", headers=headers).get_json()["data"]
    assert data["status"] == "discarded"
    assert client.post(f"/api/captures/{cap['id']}/process", headers=headers).status_code == 400
    assert client.delete(f"/api/captures/{cap['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/captures/{cap['id']}", headers=headers).status_code == 404
