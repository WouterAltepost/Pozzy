import uuid

from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.models import Email, Task
from app.modules.mail import service
from app.services import mail_classify


def _seed(server, monkeypatch):
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    service.sync_all(fetcher=server.fetch_new)
    mail_classify.classify_pending()
    return {e.uid: e for e in db.session.scalars(select(Email)).all()}


def test_routes_require_auth(client):
    assert client.get("/api/mail/emails").status_code == 401
    assert client.get("/api/mail/accounts").status_code == 401
    assert client.post("/api/mail/sync").status_code == 401


def test_unified_inbox_sorted_by_priority_then_date(client, headers, server, monkeypatch):
    _seed(server, monkeypatch)
    res = client.get("/api/mail/emails", headers=headers)
    assert res.status_code == 200
    items = res.get_json()["data"]
    assert len(items) == 5
    priorities = [i["priority"] for i in items]
    assert priorities == sorted(priorities)
    p3 = [i for i in items if i["priority"] == 3]
    dates = [i["date"] for i in p3]
    assert dates == sorted(dates, reverse=True)
    assert {i["account"]["label"] for i in items} == {"Mail 1", "Personal", "Important", "Work"}
    assert "snippet" not in items[0]
    assert items[0]["gmail_url"].startswith("https://mail.google.com/mail/u/")


def test_filters(client, headers, server, monkeypatch, areas):
    rows = _seed(server, monkeypatch)
    account_id = str(rows[101].account_id)
    assert len(client.get(f"/api/mail/emails?account_id={account_id}", headers=headers).get_json()["data"]) == 2
    assert len(client.get("/api/mail/emails?category=newsletter", headers=headers).get_json()["data"]) == 1
    assert len(client.get("/api/mail/emails?priority=4", headers=headers).get_json()["data"]) == 2
    assert len(client.get(f"/api/mail/emails?area_id={areas['Study']}", headers=headers).get_json()["data"]) == 1
    assert len(client.get("/api/mail/emails?needs_reply=1", headers=headers).get_json()["data"]) == 0
    assert len(client.get("/api/mail/emails?q=invoice", headers=headers).get_json()["data"]) == 1
    assert client.get("/api/mail/emails?category=nope", headers=headers).status_code == 400
    assert client.get("/api/mail/emails?priority=9", headers=headers).status_code == 400
    # handled defaults to unhandled only; handled=all shows everything.
    service.update_email(rows[101], {"handled": True})
    assert len(client.get("/api/mail/emails", headers=headers).get_json()["data"]) == 4
    assert len(client.get("/api/mail/emails?handled=1", headers=headers).get_json()["data"]) == 1
    assert len(client.get("/api/mail/emails?handled=all", headers=headers).get_json()["data"]) == 5


def test_get_patch_and_counts(client, headers, server, monkeypatch, areas):
    rows = _seed(server, monkeypatch)
    email_id = str(rows[102].id)
    res = client.get(f"/api/mail/emails/{email_id}", headers=headers)
    body = res.get_json()["data"]
    assert body["snippet"].startswith("Shipped!")
    assert body["task_id"] is None
    assert body["priority"] == 4

    res = client.patch(
        f"/api/mail/emails/{email_id}",
        headers=headers,
        json={"priority_override": 1, "category_override": "client", "area_override_id": areas["Work"]},
    )
    assert res.status_code == 200
    body = res.get_json()["data"]
    assert body["priority"] == 1 and body["category"] == "client" and body["area_id"] == areas["Work"]
    assert body["raw"] == {"priority": 4, "category": "notification", "area_id": None}

    # Clearing an override with null.
    body = client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={"priority_override": None}).get_json()["data"]
    assert body["priority"] == 4 and body["overrides"]["priority"] is None

    assert client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={"priority_override": 9}).status_code == 400
    assert client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={"category_override": "spam"}).status_code == 400
    assert client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={"area_override_id": str(uuid.uuid4())}).status_code == 400
    assert client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={}).status_code == 400
    assert client.patch(f"/api/mail/emails/{uuid.uuid4()}", headers=headers, json={"handled": True}).status_code == 404

    body = client.patch(f"/api/mail/emails/{email_id}", headers=headers, json={"handled": True}).get_json()["data"]
    assert body["handled"] is True and body["handled_at"]
    counts = client.get("/api/mail/counts", headers=headers).get_json()["data"]
    assert counts == {"unhandled": 4, "needs_reply": 0, "unclassified": 0}


def test_top_emails_excludes_handled(client, headers, server, monkeypatch):
    rows = _seed(server, monkeypatch)
    service.update_email(rows[101], {"handled": True})
    items = client.get("/api/mail/top?limit=3", headers=headers).get_json()["data"]
    assert len(items) == 3
    assert all(not i["handled"] for i in items)
    assert items[0]["priority"] <= items[-1]["priority"]


def test_task_from_email_uses_tasks_service_and_is_idempotent(client, headers, server, monkeypatch, areas):
    rows = _seed(server, monkeypatch)
    email = rows[101]
    service.update_email(email, {"priority_override": 1})
    res = client.post(f"/api/mail/emails/{email.id}/task", headers=headers, json={"due_date": "2026-09-20"})
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["created"] is True
    task = data["task"]
    assert task["title"] == "Invoice question"
    assert task["source"] == "email" and task["source_ref"] == str(email.id)
    assert task["urgent"] is True and task["important"] is True and task["quadrant"] == "do"
    assert task["due_date"] == "2026-09-20"
    assert task["area_id"] == areas["Personal"]
    assert "Open in Gmail: https://mail.google.com" in task["description"]
    assert "alice@client.com" in task["description"]
    assert task["tags"] == ["email"]

    again = client.post(f"/api/mail/emails/{email.id}/task", headers=headers)
    assert again.status_code == 200
    assert again.get_json()["data"]["created"] is False
    assert again.get_json()["data"]["task"]["id"] == task["id"]
    assert db.session.scalar(select(Task).where(Task.source == "email")).id == uuid.UUID(task["id"])
    assert client.get(f"/api/mail/emails/{email.id}", headers=headers).get_json()["data"]["task_id"] == task["id"]

    # The task shows up in A's task list with the email source.
    tasks = client.get("/api/tasks", headers=headers).get_json()["data"]
    assert any(t["id"] == task["id"] for t in tasks)


def test_reclassify_route(client, headers, server, monkeypatch):
    rows = _seed(server, monkeypatch)
    email = rows[201]
    monkeypatch.setattr(
        claude_client,
        "classify_emails",
        lambda batch: [{"id": str(email.id), "priority": 2, "category": "other", "area": None, "needs_reply": True, "one_line_summary": "Read this."}],
        raising=False,
    )
    body = client.post(f"/api/mail/emails/{email.id}/reclassify", headers=headers).get_json()["data"]
    assert body["classifier"] == "claude" and body["priority"] == 2 and body["needs_reply"] is True


def test_accounts_routes(client, headers, mail_env, monkeypatch):
    items = client.get("/api/mail/accounts", headers=headers).get_json()["data"]
    assert [a["label"] for a in items] == ["Mail 1", "Personal", "Important", "Work"]
    assert "password" not in items[0]
    account_id = items[0]["id"]

    body = client.patch(f"/api/mail/accounts/{account_id}", headers=headers, json={"enabled": False, "label": "Main", "color": "#000000"}).get_json()["data"]
    assert body["enabled"] is False and body["label"] == "Main"
    assert client.patch(f"/api/mail/accounts/{account_id}", headers=headers, json={}).status_code == 400
    assert client.patch(f"/api/mail/accounts/{uuid.uuid4()}", headers=headers, json={"enabled": True}).status_code == 404

    monkeypatch.setattr(service.imap_client, "test_login", lambda e, p, h: {"messages": 12, "uidnext": 13})
    res = client.post(f"/api/mail/accounts/{account_id}/test", headers=headers)
    assert res.status_code == 200 and res.get_json()["data"]["messages"] == 12
    assert res.get_json()["data"]["account"]["last_error"] is None

    def boom(e, p, h):
        raise ConnectionError("bad password")

    monkeypatch.setattr(service.imap_client, "test_login", boom)
    res = client.post(f"/api/mail/accounts/{account_id}/test", headers=headers)
    assert res.status_code == 502
    assert "bad password" in res.get_json()["error"]["message"]
    assert "bad password" in client.get("/api/mail/accounts", headers=headers).get_json()["data"][0]["last_error"]


def test_sync_now_route(client, headers, server, monkeypatch):
    monkeypatch.setattr(service.imap_client, "fetch_new", server.fetch_new)
    monkeypatch.setattr(claude_client, "classify_emails", lambda batch: None, raising=False)
    res = client.post("/api/mail/sync", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert sum(a["inserted"] for a in data["accounts"]) == 5
    assert data["classified"]["classified"] == 5
    assert data["counts"]["unhandled"] == 5
    # Running again changes nothing.
    data = client.post("/api/mail/sync", headers=headers).get_json()["data"]
    assert sum(a["inserted"] for a in data["accounts"]) == 0
