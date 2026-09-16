"""Plan the week: deterministic placement in free working slots, Claude only picks among offered options."""
import json
from datetime import date, timedelta

from app.modules.ai import planner


def _next_monday():
    t = date.today()
    return t + timedelta(days=(7 - t.weekday()) % 7 or 7)


def test_plan_places_tasks_in_working_window_without_ai(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_enabled": {"scheduling": False}}, headers=headers)
    monday = _next_monday()
    client.post("/api/tasks", json={"title": "Write report", "due_date": (monday + timedelta(days=2)).isoformat(), "estimated_minutes": 90, "urgent": True, "important": True}, headers=headers)
    client.post("/api/tasks", json={"title": "Call bank", "estimated_minutes": 30}, headers=headers)
    client.post("/api/goals", json={"title": "Run 3x", "week_start": monday.isoformat()}, headers=headers)
    data = client.post("/api/ai/plan", json={"start": monday.isoformat(), "days": 7}, headers=headers).get_json()["data"]
    titles = [i["title"] for i in data["items"]]
    assert "Write report" in titles and "Call bank" in titles
    report = next(i for i in data["items"] if i["title"] == "Write report")
    assert report["kind"] == "task" and report["task_id"] and report["minutes"] == 90 and report["ranked_by"] == "deterministic"
    assert report["start"] < report["end"] and report["start"][:10] <= (monday + timedelta(days=2)).isoformat()
    hour = int(report["start"][11:13])
    assert 8 <= hour < 18 and "before the due date" in report["reason"].lower()
    # No two suggestions overlap.
    spans = sorted((i["start"], i["end"]) for i in data["items"])
    assert all(spans[k][1] <= spans[k + 1][0] for k in range(len(spans) - 1))
    assert fake_claude.calls == []
    # Nothing was written.
    tasks = client.get("/api/tasks", headers=headers).get_json()["data"]
    assert all(t["scheduled_start"] is None for t in tasks)


def test_plan_lets_claude_choose_only_offered_options(client, headers, fake_claude):
    monday = _next_monday()
    client.post("/api/tasks", json={"title": "Write report", "estimated_minutes": 60}, headers=headers)
    # Answer with a valid pick for the first item and an invented index that must be ignored.
    def reply_for_payload():
        sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
        return sent
    fake_claude.reply = json.dumps({"items": []})
    first = client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers).get_json()["data"]
    sent = reply_for_payload()
    assert sent["items"][0]["title"] == "Write report" and len(sent["items"][0]["options"]) >= 1
    item_id = sent["items"][0]["id"]
    fake_claude.reply = json.dumps({"items": [{"id": item_id, "option": 99, "reason": "nope"}]})
    data = client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers).get_json()["data"]
    it = data["items"][0]
    assert it["start"] == first["items"][0]["start"]
    assert it["ranked_by"] == "claude" and it["reason"] != "nope"
    fake_claude.reply = json.dumps({"items": [{"id": "unknown", "option": 0, "reason": "x"}]})
    data = client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers).get_json()["data"]
    assert data["items"][0]["ranked_by"] == "deterministic"


def test_plan_validates_input(client, headers):
    assert client.post("/api/ai/plan", json={"days": 99}, headers=headers).status_code == 400
    assert client.post("/api/ai/plan", json={}).status_code == 401
    assert client.post("/api/ai/plan", json={"start": "2026-09-14", "days": 3}, headers=headers).get_json()["data"]["days"] == 3
