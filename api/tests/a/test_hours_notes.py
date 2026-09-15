from datetime import date

from app.utils import dates


def test_hours_crud_and_week_summary(client, headers, areas, monkeypatch):
    today = date(2026, 9, 16)
    monkeypatch.setattr(dates, "today_local", lambda now=None: today)
    from app.modules.hours import routes, service

    monkeypatch.setattr(service, "today_local", lambda now=None: today)
    monkeypatch.setattr(routes, "today_local", lambda now=None: today)  # the route defaults a missing date too

    res = client.post("/api/hours", json={"date": "2026-09-14", "minutes": 120, "area_id": areas["Work"], "tags": ["UDefine"]}, headers=headers)
    assert res.status_code == 201, res.get_json()
    log = res.get_json()["data"]
    client.post("/api/hours", json={"date": "2026-09-15", "minutes": 60, "area_id": areas["Work"]}, headers=headers)
    client.post("/api/hours", json={"date": "2026-09-15", "minutes": 30, "area_id": areas["Study"]}, headers=headers)
    client.post("/api/hours", json={"date": "2026-09-08", "minutes": 999, "area_id": areas["Study"]}, headers=headers)  # last week
    client.post("/api/hours", json={"minutes": 15}, headers=headers)  # today, no area
    assert client.post("/api/hours", json={"minutes": 0}, headers=headers).status_code == 400
    assert client.post("/api/hours", json={"minutes": 10, "task_id": "00000000-0000-0000-0000-000000000000"}, headers=headers).status_code == 400

    logs = client.get("/api/hours", headers=headers).get_json()["data"]
    assert len(logs) == 4  # current week only

    summary = client.get("/api/hours/week", headers=headers).get_json()["data"]
    assert summary["week_start"] == "2026-09-14"
    by = {r["area"]: r for r in summary["areas"]}
    assert by["Work"]["minutes"] == 180 and by["Work"]["target_minutes"] == 960
    assert by["Study"]["minutes"] == 30 and by["Study"]["target_minutes"] is None
    assert by["Unassigned"]["minutes"] == 15
    assert summary["total_minutes"] == 225
    assert summary["per_day"]["2026-09-15"] == 90

    upd = client.patch(f"/api/hours/{log['id']}", json={"minutes": 90, "note": "sprint"}, headers=headers).get_json()["data"]
    assert upd["minutes"] == 90 and upd["note"] == "sprint"
    assert client.delete(f"/api/hours/{log['id']}", headers=headers).status_code == 200
    assert client.delete(f"/api/hours/{log['id']}", headers=headers).status_code == 404


def test_notes_crud_filters_and_pinned_first(client, headers, areas):
    a = client.post("/api/notes", json={"title": "Alpha", "body": "first note", "tags": ["idea"]}, headers=headers).get_json()["data"]
    b = client.post("/api/notes", json={"title": "Beta", "body": "second", "area_id": areas["Study"], "pinned": True}, headers=headers).get_json()["data"]
    assert a["body"] == "first note" and a["tags"] == ["idea"]
    assert client.post("/api/notes", json={"body": "x"}, headers=headers).status_code == 400

    titles = [n["title"] for n in client.get("/api/notes", headers=headers).get_json()["data"]]
    assert titles == ["Beta", "Alpha"]
    assert [n["title"] for n in client.get("/api/notes?tag=idea", headers=headers).get_json()["data"]] == ["Alpha"]
    assert [n["title"] for n in client.get(f"/api/notes?area_id={areas['Study']}", headers=headers).get_json()["data"]] == ["Beta"]
    assert [n["title"] for n in client.get("/api/notes?q=second", headers=headers).get_json()["data"]] == ["Beta"]

    upd = client.patch(f"/api/notes/{a['id']}", json={"pinned": True, "body": "edited"}, headers=headers).get_json()["data"]
    assert upd["pinned"] is True and upd["body"] == "edited"
    assert client.get(f"/api/notes/{b['id']}", headers=headers).status_code == 200
    assert client.delete(f"/api/notes/{b['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/notes/{b['id']}", headers=headers).status_code == 404
