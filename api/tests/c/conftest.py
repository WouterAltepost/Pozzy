"""Stream C fixtures: raw RFC822 messages, a fake fetcher standing in for imap_client.fetch_new,
and a MAIL_ACCOUNTS_JSON with four accounts. No live IMAP calls in pytest."""
import json

import pytest
from imap_tools import MailMessage

from app.extensions import db
from app.integrations.imap_client import normalize_message
from app.models import Area
from conftest import bearer
from sqlalchemy import select

RAW_MULTIPART = b"""From: Alice Example <alice@client.com>
To: Wout <wout@example.com>
Subject: Invoice question
Date: Mon, 14 Sep 2026 10:15:00 +0200
Message-ID: <multi-1@client.com>
Content-Type: multipart/mixed; boundary="outer"

--outer
Content-Type: multipart/alternative; boundary="inner"

--inner
Content-Type: text/plain; charset=utf-8

Hi Wout,

Could you send the invoice for August?

Thanks, Alice
--inner
Content-Type: text/html; charset=utf-8

<html><body><p>Hi Wout,</p><p>Could you send the <b>invoice</b> for August?</p></body></html>
--inner--
--outer
Content-Type: application/pdf; name="big.pdf"
Content-Disposition: attachment; filename="big.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjQK
--outer--
"""

RAW_HTML_ONLY = b"""From: Shop <noreply@shop.example>
To: wout@example.com
Subject: Your order shipped
Date: Sun, 13 Sep 2026 18:00:00 +0000
Message-ID: <html-1@shop.example>
Content-Type: text/html; charset=utf-8

<html><head><style>p{color:red}</style></head><body><h1>Shipped!</h1><p>Your order &amp; tracking:<br>NL123</p><script>alert(1)</script></body></html>
"""

RAW_LATIN1_SUBJECT = b"""From: =?iso-8859-1?Q?J=F6rg_M=FCller?= <jorg@uni.example>
To: wout@example.com
Subject: =?iso-8859-1?Q?Pr=FCfung_n=E4chste_Woche?=
Date: Sat, 12 Sep 2026 09:30:00 +0200
Message-ID: <latin-1@uni.example>
Content-Type: text/plain; charset=iso-8859-1
Content-Transfer-Encoding: 8bit

Hallo, die Pr\xfcfung ist n\xe4chste Woche.
"""

RAW_NO_DATE = b"""From: bank@finance.example
To: wout@example.com
Subject: Statement ready
Message-ID: <nodate-1@finance.example>
Content-Type: text/plain; charset=utf-8

Your statement is ready.
"""

RAW_NEWSLETTER = b"""From: TLDR <dan@tldrnewsletter.com>
To: wout@example.com
Subject: TLDR AI 2026-09-14
Date: Mon, 14 Sep 2026 13:39:00 +0000
Message-ID: <nl-1@tldrnewsletter.com>
List-Unsubscribe: <https://tldr.example/unsub>
Content-Type: text/plain; charset=utf-8

Today in AI.
"""

ACCOUNTS = [
    {"label": "Mail 1", "email": "one@gmail.com", "password": "pw1", "color": "#4f46e5"},
    {"label": "Personal", "email": "two@gmail.com", "password": "pw2", "color": "#059669"},
    {"label": "Important", "email": "three@gmail.com", "password": "pw3", "color": "#d97706"},
    {"label": "Work", "email": "work@alpacaai.nl", "password": "pw4", "color": "#dc2626"},
]


def normalized(raw: bytes, uid: int, labels=None) -> dict:
    msg = MailMessage.from_bytes(raw)
    row = normalize_message(msg, labels)
    row["uid"] = uid
    return row


class FakeMailServer:
    """In-memory INBOX per account. `fetch_new` mirrors imap_client.fetch_new's signature."""

    def __init__(self):
        self.inbox: dict[str, list[dict]] = {}
        self.calls: list[dict] = []
        self.fail_for: set[str] = set()

    def add(self, email: str, raw: bytes, uid: int, labels=None):
        self.inbox.setdefault(email, []).append(normalized(raw, uid, labels))

    def fetch_new(self, email, password, *, last_uid, backfill_days=7, host="imap.gmail.com", max_messages=500, **_):
        self.calls.append({"email": email, "last_uid": last_uid, "backfill_days": backfill_days})
        if email in self.fail_for:
            raise ConnectionError(f"simulated IMAP failure for {email}")
        rows = self.inbox.get(email, [])
        if last_uid:
            rows = [r for r in rows if r["uid"] > last_uid]
        return sorted(rows, key=lambda r: r["uid"])[:max_messages]


@pytest.fixture
def headers(token_factory):
    return bearer(token_factory())


@pytest.fixture
def areas(app):
    rows = db.session.scalars(select(Area).order_by(Area.sort_order)).all()
    return {a.name: str(a.id) for a in rows}


@pytest.fixture
def mail_env(app):
    app.config["MAIL_ACCOUNTS_JSON"] = json.dumps(ACCOUNTS)
    return ACCOUNTS


@pytest.fixture
def server(mail_env):
    srv = FakeMailServer()
    srv.add("one@gmail.com", RAW_MULTIPART, 101)
    srv.add("one@gmail.com", RAW_HTML_ONLY, 102, ["\\Inbox", "Shopping"])
    srv.add("two@gmail.com", RAW_NEWSLETTER, 201)
    srv.add("three@gmail.com", RAW_LATIN1_SUBJECT, 301)
    srv.add("work@alpacaai.nl", RAW_NO_DATE, 401)
    return srv
