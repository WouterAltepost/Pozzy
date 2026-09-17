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


def test_rules_reach_every_system_prompt_and_planner_can_skip(client, headers, fake_claude):
    client.put("/api/settings", json={"ai_rules": ["Never plan anything before 09:00.", "My commute to school takes 45 minutes."], "ai_context": "Student and developer in Amsterdam."}, headers=headers)
    monday = _next_monday()
    client.post("/api/tasks", json={"title": "Deep clean room", "estimated_minutes": 60}, headers=headers)
    fake_claude.reply = json.dumps({"text": "Quiet day."})
    client.post("/api/ai/briefing", headers=headers)
    system = fake_claude.last["system"][0]["text"]
    assert system.startswith("## Standing rules from the user") and "Never plan anything before 09:00." in system and "About the user" in system and "Amsterdam" in system
    assert system.index("Standing rules") < system.index("## Task instructions") < system.index("chief of staff")
    fake_claude.reply = json.dumps({"items": []})
    client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers)
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    assert sent["rules"] == ["Never plan anything before 09:00.", "My commute to school takes 45 minutes."]
    item_id = sent["items"][0]["id"]
    fake_claude.reply = json.dumps({"items": [{"id": item_id, "option": -1, "rule_check": "all options before 09:00", "reason": "Every option is before 09:00."}]})
    data = client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers).get_json()["data"]
    assert data["items"] == []
    # place false wins even when the model also returns an index.
    fake_claude.reply = json.dumps({"items": [{"id": item_id, "place": False, "option": 0, "rule_check": "30 min before a campus class", "reason": "Commute rule."}]})
    data = client.post("/api/ai/plan", json={"start": monday.isoformat()}, headers=headers).get_json()["data"]
    assert data["items"] == []


def test_options_carry_neighbours_and_buffer_keeps_distance(client, headers, fake_claude, app):
    from datetime import datetime, timezone
    from app.extensions import db
    from app.models import CalendarAccount, CalendarEvent

    monday = _next_monday()
    client.put("/api/settings", json={"ai_enabled": {"scheduling": False}, "plan_buffer_minutes": 45}, headers=headers)
    # A class on campus from 09:30 to 12:00 on the Monday.
    acct = CalendarAccount(name="iCloud", caldav_url="https://caldav.example", username="x", secret_ref="env:x", enabled=True)
    db.session.add(acct); db.session.flush()
    start = datetime(monday.year, monday.month, monday.day, 7, 30, tzinfo=timezone.utc)  # 09:30 Amsterdam
    db.session.add(CalendarEvent(account_id=acct.id, calendar_url="c", uid="u1", title="Sprint 3 NGS", location="AM00.02.270", start=start, end=start.replace(hour=10, minute=0), all_day=False))
    db.session.commit()
    client.post("/api/tasks", json={"title": "Buy new book", "estimated_minutes": 15, "due_date": monday.isoformat()}, headers=headers)
    data = client.post("/api/ai/plan", json={"start": monday.isoformat(), "days": 1}, headers=headers).get_json()["data"]
    assert data["items"], "the task still gets a slot"
    it = data["items"][0]
    # With a 45 minute buffer the slot cannot sit inside 08:45 to 12:45 Amsterdam.
    hhmm = it["start"][11:16]
    assert not ("08:45" <= hhmm < "12:45"), it
    # With AI on, Claude sees the neighbours of every option.
    client.put("/api/settings", json={"ai_enabled": {"scheduling": True}, "plan_buffer_minutes": 0}, headers=headers)
    fake_claude.reply = json.dumps({"items": []})
    client.post("/api/ai/plan", json={"start": monday.isoformat(), "days": 1}, headers=headers)
    sent = json.loads(fake_claude.last_user_text().split("\n\nReply exactly")[0])
    opts = sent["items"][0]["options"]
    assert any((o.get("after") or {}).get("title") == "Sprint 3 NGS" or (o.get("before") or {}).get("title") == "Sprint 3 NGS" for o in opts), opts
    near = next(o for o in opts if o.get("after") and o["after"]["title"] == "Sprint 3 NGS")
    assert near["after"]["location"] == "AM00.02.270" and near["after"]["starts"] == "09:30" and isinstance(near["after"]["gap_minutes"], int)


def test_rules_become_buffers_before_the_slot_search(client, headers, fake_claude):
    from datetime import datetime, timezone
    from app.extensions import db
    from app.models import CalendarAccount, CalendarEvent

    monday = _next_monday()
    client.put("/api/settings", json={"ai_rules": ["My commute to school takes 45 minutes, so nothing right before or after a class on campus.", "Leave 1 hour free after workouts."]}, headers=headers)
    acct = CalendarAccount(name="iCloud", caldav_url="https://caldav.example", username="x", secret_ref="env:x", enabled=True)
    db.session.add(acct); db.session.flush()
    cls = datetime(monday.year, monday.month, monday.day, 7, 30, tzinfo=timezone.utc)  # 09:30 to 12:00 Amsterdam
    gym = datetime(monday.year, monday.month, monday.day, 12, 0, tzinfo=timezone.utc)  # 14:00 to 15:00 Amsterdam
    db.session.add(CalendarEvent(account_id=acct.id, calendar_url="c", uid="u1", title="Sprint 3 NGS", location="AM00.02.270", start=cls, end=cls.replace(hour=10, minute=0), all_day=False))
    db.session.add(CalendarEvent(account_id=acct.id, calendar_url="c", uid="u2", title="Workout Push Day", location="", start=gym, end=gym.replace(hour=13), all_day=False))
    db.session.commit()
    client.post("/api/tasks", json={"title": "Buy new book", "estimated_minutes": 15, "due_date": monday.isoformat()}, headers=headers)
    # First call: constraints. Second call: ranking.
    fake_claude.replies = [
        json.dumps({"earliest": "09:00", "latest": None, "blocked_days": [], "buffers": [{"index": 0, "before": 45, "after": 45, "why": "campus class"}, {"index": 1, "before": 0, "after": 60, "why": "workout"}]}),
        json.dumps({"items": []}),
    ]
    data = client.post("/api/ai/plan", json={"start": monday.isoformat(), "days": 1}, headers=headers).get_json()["data"]
    first = json.loads(fake_claude.calls[-2]["messages"][0]["content"].split("\n\nReply exactly")[0])
    assert first["rules"][0].startswith("My commute") and first["appointments"][0]["title"] == "Sprint 3 NGS" and first["appointments"][0]["location"] == "AM00.02.270"
    assert data["constraints"]["buffers"][0] == {"title": "Sprint 3 NGS", "before": 45, "after": 45, "why": "campus class"}
    assert data["items"], "a compliant slot exists later in the day"
    hhmm = data["items"][0]["start"][11:16]
    end_hhmm = data["items"][0]["end"][11:16]
    # Not before 09:00, not within 45 min of the class (08:45 to 12:45), not during or within 60 min after the workout (14:00 to 16:00).
    assert hhmm >= "09:00" and not ("08:45" <= hhmm < "12:45") and not ("14:00" <= hhmm < "16:00"), data["items"][0]
    assert not ("08:45" < end_hhmm <= "12:45") and not ("14:00" < end_hhmm <= "16:00")


def test_blocked_day_and_earliest_apply(client, headers, fake_claude):
    monday = _next_monday()
    client.put("/api/settings", json={"ai_rules": ["Never plan anything before 11:00.", "Keep Monday free."]}, headers=headers)
    client.post("/api/tasks", json={"title": "Call bank", "estimated_minutes": 30}, headers=headers)
    # Constraints need at least one appointment to be asked; without appointments the planner skips the call and only the window applies.
    from datetime import datetime, timezone
    from app.extensions import db
    from app.models import CalendarAccount, CalendarEvent
    acct = CalendarAccount(name="iCloud", caldav_url="https://caldav.example", username="x", secret_ref="env:x", enabled=True)
    db.session.add(acct); db.session.flush()
    ev = datetime(monday.year, monday.month, monday.day + 1, 10, 0, tzinfo=timezone.utc)
    db.session.add(CalendarEvent(account_id=acct.id, calendar_url="c", uid="u9", title="Dentist", location="", start=ev, end=ev.replace(hour=11), all_day=False))
    db.session.commit()
    fake_claude.replies = [json.dumps({"earliest": "11:00", "latest": None, "blocked_days": [monday.isoformat()], "buffers": []}), json.dumps({"items": []})]
    data = client.post("/api/ai/plan", json={"start": monday.isoformat(), "days": 2}, headers=headers).get_json()["data"]
    assert data["items"] and data["items"][0]["start"][:10] != monday.isoformat() and data["items"][0]["start"][11:16] >= "11:00"
