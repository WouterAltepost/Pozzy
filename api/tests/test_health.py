from datetime import datetime


def test_health_is_public_and_reports_db(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert body["data"]["db"] is True
    parsed = datetime.fromisoformat(body["data"]["time"])
    assert parsed.tzinfo is not None


def test_unknown_route_uses_envelope(client):
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    body = res.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
