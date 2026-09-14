import json

from app.extensions import db
from app.models import MailAccount
from app.modules.mail.service import upsert_accounts_from_env

ENV = json.dumps([{"label": "Work", "email": "wout@alpacaai.nl", "password": "x", "color": "#123456"}])


def test_accounts_missing_from_env_are_disabled(app):
    app.config["MAIL_ACCOUNTS_JSON"] = ENV
    stale = MailAccount(email="wout@alpacaai", label="Work", color="#000000", imap_host="imap.gmail.com", secret_ref="env:wout@alpacaai", enabled=True, sort_order=9)
    db.session.add(stale)
    db.session.commit()

    rows = {a.email: a for a in upsert_accounts_from_env()}
    assert rows["wout@alpacaai.nl"].enabled is True
    assert rows["wout@alpacaai"].enabled is False
    assert "Not in MAIL_ACCOUNTS_JSON" in rows["wout@alpacaai"].last_error

    # Idempotent, and a UI-disabled env account stays disabled.
    rows["wout@alpacaai.nl"].enabled = False
    db.session.commit()
    rows = {a.email: a for a in upsert_accounts_from_env()}
    assert rows["wout@alpacaai.nl"].enabled is False and rows["wout@alpacaai"].enabled is False
