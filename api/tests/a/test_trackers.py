from datetime import date, timedelta

from app.utils import dates


def _tracker(client, headers, **kw):
    body = {"name": "Creatine", "type": "daily_bool"}
    body.update(kw)
    res = client.post("/api/trackers", json=body, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_tracker_crud_and_type_rules(client, headers, areas):
    t = _tracker(client, headers, area_id=areas["Health"])
    assert t["target_value"] == 1 and t["target_period"] == "day" and t["sort_order"] == 1
    c = _tracker(client, headers, name="Vitamins", type="weekly_count", target_value=3)
    assert c["target_period"] == "week" and c["sort_order"] == 2
    assert client.post("/api/trackers", json={"name": "x", "type": "bogus"}, headers=headers).status_code == 400
    assert client.post("/api/trackers", json={"type": "numeric"}, headers=headers).status_code == 400

    upd = client.patch(f"/api/trackers/{t['id']}", json={"active": False, "name": "Creatine 5g"}, headers=headers).get_json()["data"]
    assert upd["active"] is False
    assert [x["name"] for x in client.get("/api/trackers", headers=headers).get_json()["data"]] == ["Vitamins"]
    assert len(client.get("/api/trackers?include_inactive=1", headers=headers).get_json()["data"]) == 2
    assert client.delete(f"/api/trackers/{t['id']}", headers=headers).status_code == 200
    assert client.delete(f"/api/trackers/{t['id']}", headers=headers).status_code == 404


def test_entries_upsert_tick_and_delete(client, headers):
    b = _tracker(client, headers)
    c = _tracker(client, headers, name="Vitamins", type="weekly_count", target_value=3)
    w = _tracker(client, headers, name="Weight", type="numeric", unit="kg")

    e = client.post(f"/api/trackers/{b['id']}/tick", json={"date": "2026-09-14"}, headers=headers).get_json()["data"]
    assert e["value"] == 1
    e = client.post(f"/api/trackers/{b['id']}/tick", json={"date": "2026-09-14"}, headers=headers).get_json()["data"]
    assert e["value"] == 0
    for _ in range(2):
        e = client.post(f"/api/trackers/{c['id']}/tick", json={"date": "2026-09-14"}, headers=headers).get_json()["data"]
    assert e["value"] == 2

    e = client.put(f"/api/trackers/{w['id']}/entries", json={"date": "2026-09-14", "value": 78.4, "note": "morning"}, headers=headers).get_json()["data"]
    assert e["value"] == 78.4 and e["note"] == "morning"
    e = client.put(f"/api/trackers/{w['id']}/entries", json={"date": "2026-09-14", "value": 78.0}, headers=headers).get_json()["data"]
    assert e["value"] == 78.0 and e["note"] == "morning"
    assert client.put(f"/api/trackers/{w['id']}/entries", json={"date": "2026-09-14", "value": -1}, headers=headers).status_code == 400
    assert client.put(f"/api/trackers/{w['id']}/entries", json={"date": "2026-09-14"}, headers=headers).status_code == 400

    assert client.delete(f"/api/trackers/{w['id']}/entries/2026-09-14", headers=headers).status_code == 200
    assert client.delete(f"/api/trackers/{w['id']}/entries/2026-09-14", headers=headers).status_code == 404


def test_week_grid_completion_and_streaks(client, headers, monkeypatch):
    today = date(2026, 9, 17)  # Thursday
    monkeypatch.setattr(dates, "today_local", lambda now=None: today)
    from app.modules.trackers import service

    monkeypatch.setattr(service, "today_local", lambda now=None: today)

    b = _tracker(client, headers)
    c = _tracker(client, headers, name="Sauna", type="weekly_count", target_value=1)
    n = _tracker(client, headers, name="Sleep", type="numeric", target_value=7, target_period="day", unit="h")

    # Bool: ticked Mon, Tue, Wed and the Sunday before (streak 4 despite Thursday not yet ticked).
    for d in ("2026-09-13", "2026-09-14", "2026-09-15", "2026-09-16"):
        client.post(f"/api/trackers/{b['id']}/tick", json={"date": d}, headers=headers)
    client.post(f"/api/trackers/{c['id']}/tick", json={"date": "2026-09-15"}, headers=headers)
    client.post(f"/api/trackers/{c['id']}/tick", json={"date": "2026-09-08"}, headers=headers)  # previous week met too
    client.put(f"/api/trackers/{n['id']}/entries", json={"date": "2026-09-14", "value": 7.5}, headers=headers)
    client.put(f"/api/trackers/{n['id']}/entries", json={"date": "2026-09-15", "value": 6}, headers=headers)

    grid = client.get("/api/trackers/week?week_start=2026-09-17", headers=headers).get_json()["data"]
    assert grid["week_start"] == "2026-09-14" and grid["week_end"] == "2026-09-20"
    rows = {r["name"]: r for r in grid["trackers"]}
    assert [d["date"] for d in rows["Creatine"]["days"]][0] == "2026-09-14"
    assert [d["met"] for d in rows["Creatine"]["days"]] == [True, True, True, False, False, False, False]
    assert rows["Creatine"]["completion"] == 0.75  # 3 of 4 elapsed days
    assert rows["Creatine"]["streak"] == 4
    assert rows["Sauna"]["week_total"] == 1 and rows["Sauna"]["completion"] == 1.0 and rows["Sauna"]["streak"] == 2
    assert rows["Sleep"]["days"][0]["met"] is True and rows["Sleep"]["days"][1]["met"] is False
    assert rows["Sleep"]["streak"] == 0

    # Past week: completion uses all 7 days.
    grid = client.get("/api/trackers/week?week_start=2026-09-07", headers=headers).get_json()["data"]
    assert {r["name"]: r["completion"] for r in grid["trackers"]}["Sauna"] == 1.0

    hist = client.get(f"/api/trackers/{n['id']}/history?weeks=2", headers=headers).get_json()["data"]
    assert [p["value"] for p in hist["points"]] == [7.5, 6]
    assert len(hist["weekly"]) == 2 and hist["weekly"][1]["avg"] == 6.75
    # Whole run: an entry backdated far before creation widens the range to that week.
    client.put(f"/api/trackers/{n['id']}/entries", json={"date": "2026-06-03", "value": 5}, headers=headers)
    hist = client.get(f"/api/trackers/{n['id']}/history?all=1", headers=headers).get_json()["data"]
    assert hist["from"] == "2026-06-01" and hist["points"][0]["value"] == 5 and hist["weeks"] == len(hist["weekly"]) >= 15


def test_series_covers_every_tracker_on_one_range(client, headers):
    b = client.post("/api/trackers", json={"name": "Sauna", "type": "daily_bool"}, headers=headers).get_json()["data"]
    w = client.post("/api/trackers", json={"name": "Weight", "type": "numeric", "unit": "kg", "target_value": 80, "target_period": "day"}, headers=headers).get_json()["data"]
    monday = (date.today() - timedelta(days=date.today().weekday())).isoformat()  # this week, whatever today is
    client.post(f"/api/trackers/{b['id']}/tick", json={"date": monday}, headers=headers)
    client.put(f"/api/trackers/{w['id']}/entries", json={"date": monday, "value": 81.5}, headers=headers)
    client.put(f"/api/trackers/{w['id']}/entries", json={"date": (date.today() - timedelta(days=80)).isoformat(), "value": 84}, headers=headers)
    data = client.get("/api/trackers/series?weeks=2", headers=headers).get_json()["data"]
    assert data["weeks"] == 2 and {s["tracker"]["name"] for s in data["series"]} == {"Sauna", "Weight"}
    sauna = next(s for s in data["series"] if s["tracker"]["name"] == "Sauna")
    assert sauna["weekly"][-1]["met_days"] == 1 and len(sauna["weekly"]) == 2
    weight = next(s for s in data["series"] if s["tracker"]["name"] == "Weight")
    assert [p["value"] for p in weight["points"]] == [81.5] and weight["weekly"][-1]["met_days"] is None
    data = client.get("/api/trackers/series?weeks=all", headers=headers).get_json()["data"]
    assert data["from"] <= (date.today() - timedelta(days=80)).isoformat() and data["weeks"] >= 11
    weight = next(s for s in data["series"] if s["tracker"]["name"] == "Weight")
    assert [p["value"] for p in weight["points"]] == [84, 81.5]


def test_untick_reverses_one_tap_and_entry_endpoints_return_the_row(client, headers):
    """A mis-tap on a count cell can be taken back: untick subtracts one, removes the entry at
    zero, toggles a bool back. Every entry endpoint answers with the tracker's grid row."""
    count = _tracker(client, headers, name="Vitamins", type="weekly_count", target_value=3)
    day = date.today().isoformat()
    first = client.post(f"/api/trackers/{count['id']}/tick", json={"date": day}, headers=headers).get_json()["data"]
    assert first["value"] == 1 and first["row"]["week_total"] == 1
    assert [d["value"] for d in first["row"]["days"] if d["date"] == day] == [1]
    client.post(f"/api/trackers/{count['id']}/tick", json={"date": day}, headers=headers)

    back = client.post(f"/api/trackers/{count['id']}/untick", json={"date": day}, headers=headers).get_json()["data"]
    assert back["value"] == 1 and back["row"]["week_total"] == 1
    gone = client.post(f"/api/trackers/{count['id']}/untick", json={"date": day}, headers=headers).get_json()["data"]
    assert gone["value"] is None and gone["row"]["week_total"] == 0
    assert [d["value"] for d in gone["row"]["days"] if d["date"] == day] == [None]
    # Nothing left to take back: still a clean answer, no 404.
    again = client.post(f"/api/trackers/{count['id']}/untick", json={"date": day}, headers=headers)
    assert again.status_code == 200 and again.get_json()["data"]["value"] is None

    habit = _tracker(client, headers, name="Creatine", type="daily_bool")
    on = client.post(f"/api/trackers/{habit['id']}/tick", json={"date": day}, headers=headers).get_json()["data"]
    assert on["value"] == 1 and on["row"]["days"][date.today().weekday()]["met"] is True
    off = client.post(f"/api/trackers/{habit['id']}/untick", json={"date": day}, headers=headers).get_json()["data"]
    assert off["value"] == 0 and off["row"]["days"][date.today().weekday()]["met"] is False

    weight = _tracker(client, headers, name="Sauna", type="duration", target_value=20, target_period="day", unit="min")
    put = client.put(f"/api/trackers/{weight['id']}/entries", json={"date": day, "value": 45}, headers=headers).get_json()["data"]
    assert put["value"] == 45 and put["row"]["week_total"] == 45
    less = client.post(f"/api/trackers/{weight['id']}/untick", json={"date": day}, headers=headers).get_json()["data"]
    assert less["value"] == 25
    deleted = client.delete(f"/api/trackers/{weight['id']}/entries/{day}", headers=headers).get_json()["data"]
    assert deleted["deleted"] == day and deleted["row"]["week_total"] == 0
