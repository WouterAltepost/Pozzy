from conftest import bearer


def test_settings_round_trip(client, token_factory):
    headers = bearer(token_factory())

    res = client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["timezone"] == "Europe/Amsterdam"
    assert data["week_start"] == 1
    assert data["working_window"] == {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00"}
    assert data["ai_enabled"]["mail_classify"] is True
    assert data["hour_targets"] == {"Work": 960}

    res = client.put(
        "/api/settings",
        json={"timezone": "UTC", "briefing_time": "07:00", "hour_targets": {"Work": 600, "Study": 300}},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["timezone"] == "UTC"
    assert data["briefing_time"] == "07:00"
    assert data["hour_targets"] == {"Work": 600, "Study": 300}
    assert data["week_start"] == 1  # untouched keys survive

    res = client.get("/api/settings", headers=headers)
    assert res.get_json()["data"]["timezone"] == "UTC"


def test_settings_requires_auth(client):
    assert client.get("/api/settings").status_code == 401
    assert client.put("/api/settings", json={"a": 1}).status_code == 401


def test_settings_rejects_bad_body(client, token_factory):
    headers = bearer(token_factory())
    assert client.put("/api/settings", json=[1, 2], headers=headers).status_code == 400
    assert client.put("/api/settings", json={}, headers=headers).status_code == 400
    assert client.put("/api/settings", data="nope", headers=headers).status_code == 400
    res = client.put("/api/settings", json={"": 1}, headers=headers)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"
