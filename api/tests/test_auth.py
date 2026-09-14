import time

from cryptography.hazmat.primitives.asymmetric import ec

from conftest import JWT_SECRET, bearer, make_token


def _error_code(response):
    return response.get_json()["error"]["code"]


def test_valid_es256_token_passes(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(sub="user-1", email="wout@example.com")))
    assert res.status_code == 200
    assert res.get_json() == {"data": {"id": "user-1", "email": "wout@example.com"}, "error": None}


def test_missing_token_is_401(client):
    res = client.get("/api/me")
    assert res.status_code == 401
    assert _error_code(res) == "unauthorized"
    assert res.get_json()["data"] is None


def test_non_bearer_header_is_401(client, token_factory):
    res = client.get("/api/me", headers={"Authorization": f"Basic {token_factory()}"})
    assert res.status_code == 401


def test_expired_token_is_401(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(exp=int(time.time()) - 10)))
    assert res.status_code == 401
    assert "expired" in res.get_json()["error"]["message"].lower()


def test_wrong_signing_key_is_401(client):
    other_key = ec.generate_private_key(ec.SECP256R1())
    res = client.get("/api/me", headers=bearer(make_token(other_key)))
    assert res.status_code == 401


def test_unknown_kid_is_401(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(kid="nope")))
    assert res.status_code == 401


def test_wrong_audience_is_401(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(aud="anon")))
    assert res.status_code == 401


def test_garbage_token_is_401(client):
    res = client.get("/api/me", headers=bearer("not.a.jwt"))
    assert res.status_code == 401


def test_valid_hs256_token_with_project_secret_passes(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(alg="HS256", secret=JWT_SECRET, sub="hs")))
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == "hs"


def test_hs256_with_wrong_secret_is_401(client, token_factory):
    res = client.get("/api/me", headers=bearer(token_factory(alg="HS256", secret="wrong-secret-that-is-also-thirty-two-bytes")))
    assert res.status_code == 401


def test_areas_requires_auth_and_is_seeded(client, token_factory):
    assert client.get("/api/areas").status_code == 401
    res = client.get("/api/areas", headers=bearer(token_factory()))
    assert res.status_code == 200
    names = [a["name"] for a in res.get_json()["data"]]
    assert names == ["Study", "Work", "Personal", "Health"]
