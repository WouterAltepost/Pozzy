"""Habit schedules, skips, schedule-aware streaks, stats and reorder."""
from datetime import date, timedelta

import pytest

from app.utils import dates

TODAY = date(2026, 10, 15)  # Thursday


@pytest.fixture
def frozen(monkeypatch):
    from app.modules.trackers import service

    monkeypatch.setattr(dates, "today_local", lambda now=None: TODAY)
    monkeypatch.setattr(service, "today_local", lambda now=None: TODAY)
    return TODAY


def _new(client, headers, **kw):
    body = {"name": "Gym", "type": "daily_bool"}
    body.update(kw)
    res = client.post("/api/trackers", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def _tick(client, headers, t, day):
    return client.post(f"/api/trackers/{t['id']}/tick", json={"date": day.isoformat()}, headers=headers).get_json()["data"]


def _row(client, headers, name, week=TODAY):
    grid = client.get(f"/api/trackers/week?week_start={week.isoformat()}", headers=headers).get_json()["data"]
    return next(r for r in grid["trackers"] if r["name"] == name)


MON_WED_FRI = 0b0010101


def test_schedule_validation(client, headers):
    assert client.post("/api/trackers", json={"name": "x", "type": "daily_bool", "schedule": "weekdays"}, headers=headers).status_code == 400
    assert client.post("/api/trackers", json={"name": "x", "type": "daily_bool", "schedule": "every_n_days", "schedule_n": 1}, headers=headers).status_code == 400
    assert client.post("/api/trackers", json={"name": "x", "type": "daily_bool", "reminder_time": "25:00"}, headers=headers).status_code == 400
    t = _new(client, headers, schedule="weekdays", schedule_days=MON_WED_FRI, schedule_n=4, reminder_time="07:30", icon="barbell")
    assert t["schedule"] == "weekdays" and t["schedule_days"] == MON_WED_FRI and t["schedule_n"] is None
    assert t["reminder_time"] == "07:30" and t["icon"] == "barbell"
    upd = client.patch(f"/api/trackers/{t['id']}", json={"schedule": "daily"}, headers=headers).get_json()["data"]
    assert upd["schedule"] == "daily" and upd["schedule_days"] is None
    upd = client.patch(f"/api/trackers/{t['id']}", json={"reminder_time": ""}, headers=headers).get_json()["data"]
    assert upd["reminder_time"] is None


def test_weekday_schedule_due_days_streak_and_completion(client, headers, frozen):
    t = _new(client, headers, schedule="weekdays", schedule_days=MON_WED_FRI)
    # Mon, Wed, Fri of last week and Mon, Wed of this week: Tue and Thu off days never break it.
    for d in (date(2026, 10, 5), date(2026, 10, 7), date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 14)):
        _tick(client, headers, t, d)
    row = _row(client, headers, "Gym")
    assert [d["due"] for d in row["days"]] == [True, False, True, False, True, False, False]
    assert row["streak"] == 5 and row["best_streak"] == 5
    assert row["completion"] == 1.0
    assert row["next_due"] == "2026-10-16"  # today (Thu) is not due, Friday is
    # The chart divides by due days: last week 3 of 3, this week 2 of 2 so far.
    weekly = client.get("/api/trackers/series?weeks=2", headers=headers).get_json()["data"]["series"][0]["weekly"]
    assert [(w["met_days"], w["due_days"]) for w in weekly] == [(3, 3), (2, 2)]
    # Missing a due Monday breaks it.
    client.delete(f"/api/trackers/{t['id']}/entries/2026-10-12", headers=headers)
    row = _row(client, headers, "Gym")
    assert row["streak"] == 1 and row["best_streak"] == 3 and row["completion"] == 0.5


def test_every_n_days_is_flexible(client, headers, frozen):
    t = _new(client, headers, name="Sauna", schedule="every_n_days", schedule_n=3)
    # Done on the 9th and the 12th (3 days apart, fine), then the 15th is due again.
    _tick(client, headers, t, date(2026, 10, 9))
    _tick(client, headers, t, date(2026, 10, 12))
    row = _row(client, headers, "Sauna")
    by_day = {d["date"]: d["due"] for d in row["days"]}
    assert by_day["2026-10-13"] is False and by_day["2026-10-14"] is False and by_day["2026-10-15"] is True
    assert row["streak"] == 2 and row["next_due"] == "2026-10-15"
    # A 4 day gap breaks it: the 13th of a run from the 9th would have been due.
    client.delete(f"/api/trackers/{t['id']}/entries/2026-10-12", headers=headers)
    _tick(client, headers, t, date(2026, 10, 13))
    assert _row(client, headers, "Sauna")["streak"] == 1


def test_skip_keeps_the_streak_and_leaves_completion(client, headers, frozen):
    t = _new(client, headers, name="Creatine")
    for d in (date(2026, 10, 12), date(2026, 10, 14)):
        _tick(client, headers, t, d)
    assert _row(client, headers, "Creatine")["streak"] == 1
    res = client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-13", "status": "skipped", "note": "ill"}, headers=headers)
    data = res.get_json()["data"]
    assert res.status_code == 200 and data["status"] == "skipped" and data["value"] == 0 and data["note"] == "ill"
    row = data["row"]
    assert row["streak"] == 2 and row["completion"] == 1.0
    assert row["days"][1]["status"] == "skipped" and row["days"][1]["met"] is False
    # A tap on a skipped day makes it done; untick on a skipped day clears it.
    on = _tick(client, headers, t, date(2026, 10, 13))
    assert on["status"] == "done" and on["value"] == 1
    client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-13", "status": "skipped"}, headers=headers)
    off = client.post(f"/api/trackers/{t['id']}/untick", json={"date": "2026-10-13"}, headers=headers).get_json()["data"]
    assert off["value"] is None
    # Skips never count in the week total of a count habit.
    c = _new(client, headers, name="Vitamins", type="weekly_count", target_value=2)
    _tick(client, headers, c, date(2026, 10, 12))
    client.put(f"/api/trackers/{c['id']}/entries", json={"date": "2026-10-13", "status": "skipped", "value": 5}, headers=headers)
    row = _row(client, headers, "Vitamins")
    assert row["week_total"] == 1 and row["week_met"] is False


def test_note_set_and_cleared(client, headers, frozen):
    t = _new(client, headers, name="Read")
    client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-14", "value": 1, "note": "20 pages"}, headers=headers)
    e = client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-14", "value": 1, "note": ""}, headers=headers).get_json()["data"]
    assert e["note"] is None


def test_stats_streaks_rates_heatmap_and_notes(client, headers, frozen):
    t = _new(client, headers, name="Walk")
    # A 4 day run, a miss on the 5th, then 7 days up to yesterday.
    for i in range(1, 5):
        _tick(client, headers, t, date(2026, 10, i))
    for i in range(8, 15):
        _tick(client, headers, t, date(2026, 10, i))
    client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-06", "status": "skipped"}, headers=headers)
    client.put(f"/api/trackers/{t['id']}/entries", json={"date": "2026-10-10", "value": 1, "note": "rain"}, headers=headers)
    s = client.get(f"/api/trackers/{t['id']}/stats", headers=headers).get_json()["data"]
    assert s["current_streak"] == 7 and s["best_streak"] == 7 and s["unit"] == "day"
    # 11 met; 5th and 7th missed; 6th skipped and today open do not count.
    assert s["met_total"] == 11 and s["counted_total"] == 13 and s["skipped_total"] == 1
    assert s["months"][-1]["month"] == "2026-10" and s["months"][-1]["met"] == 11
    assert len(s["heatmap"]) == 53 * 7 and s["heatmap"][0]["date"] == (date(2026, 10, 12) - timedelta(weeks=52)).isoformat()
    assert [n["note"] for n in s["notes"]] == ["rain"]
    assert len(s["weekdays"]) == 7 and s["weekdays"][date(2026, 10, 5).weekday()]["counted"] >= 1
    # Week habits count in weeks.
    w = _new(client, headers, name="Sauna", type="weekly_count", target_value=1)
    for d in (date(2026, 9, 29), date(2026, 10, 6), date(2026, 10, 13)):
        _tick(client, headers, w, d)
    s = client.get(f"/api/trackers/{w['id']}/stats", headers=headers).get_json()["data"]
    assert s["unit"] == "week" and s["current_streak"] == 3 and s["weekdays"] == []


def test_reorder(client, headers):
    a = _new(client, headers, name="A")
    b = _new(client, headers, name="B")
    c = _new(client, headers, name="C")
    out = client.post("/api/trackers/reorder", json={"ids": [c["id"], a["id"]]}, headers=headers).get_json()["data"]
    assert [t["name"] for t in out] == ["C", "A", "B"]
    assert [t["name"] for t in client.get("/api/trackers", headers=headers).get_json()["data"]] == ["C", "A", "B"]
    assert client.post("/api/trackers/reorder", json={"ids": ["nope"]}, headers=headers).status_code == 400
