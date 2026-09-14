def test_goals_week_defaults_and_crud(client, headers, areas):
    res = client.post("/api/goals", json={"title": "Run 3 times", "target_value": 3, "area_id": areas["Health"], "week_start": "2026-09-16"}, headers=headers)
    assert res.status_code == 201, res.get_json()
    goal = res.get_json()["data"]
    assert goal["week_start"] == "2026-09-14"  # snapped to Monday
    assert goal["progress"] == 0 and goal["done"] is False

    data = client.get("/api/goals?week_start=2026-09-17", headers=headers).get_json()["data"]
    assert data["week_start"] == "2026-09-14" and len(data["goals"]) == 1
    assert client.get("/api/goals?week_start=2026-09-21", headers=headers).get_json()["data"]["goals"] == []

    g = client.post(f"/api/goals/{goal['id']}/progress", json={"delta": 2}, headers=headers).get_json()["data"]
    assert g["current_value"] == 2 and g["progress"] == 2 / 3 and g["done"] is False
    g = client.post(f"/api/goals/{goal['id']}/progress", json={}, headers=headers).get_json()["data"]
    assert g["current_value"] == 3 and g["done"] is True and g["progress"] == 1

    g = client.patch(f"/api/goals/{goal['id']}", json={"done": False, "notes": "almost"}, headers=headers).get_json()["data"]
    assert g["done"] is False and g["notes"] == "almost"

    assert client.post("/api/goals", json={"title": ""}, headers=headers).status_code == 400
    assert client.post("/api/goals", json={"title": "x", "target_value": "many"}, headers=headers).status_code == 400
    assert client.delete(f"/api/goals/{goal['id']}", headers=headers).status_code == 200
    assert client.patch(f"/api/goals/{goal['id']}", json={"title": "x"}, headers=headers).status_code == 404


def test_goal_without_target_is_binary(client, headers):
    goal = client.post("/api/goals", json={"title": "Ship v1"}, headers=headers).get_json()["data"]
    assert goal["progress"] is None
    g = client.patch(f"/api/goals/{goal['id']}", json={"done": True}, headers=headers).get_json()["data"]
    assert g["progress"] == 1
