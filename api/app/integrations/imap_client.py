"""Read-only IMAP client for Gmail and Google Workspace (stream C).

CLAUDE.md rule 8: this module never issues STORE, COPY, MOVE, EXPUNGE or any
flag change. Fetches use BODY.PEEK (imap-tools `mark_seen=False`), INBOX only.
Attachments are never downloaded and full bodies are never stored: every
message is reduced to headers plus a snippet by `normalize_message`.

Two layers:
- `open_mailbox`, `fetch_new`, `fetch_newest`, `test_login`: network.
- `normalize_message`, `make_snippet`, `strip_html`: pure, unit tested with
  raw RFC822 fixtures wrapped in `imap_tools.MailMessage.from_bytes`.
"""
from __future__ import annotations

import html as html_lib
import re
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from email.header import decode_header
from email.utils import getaddresses

from imap_tools import AND, MailBox, MailMessage
from imap_tools.utils import decode_value

DEFAULT_HOST = "imap.gmail.com"
SNIPPET_BYTES = 2048
CONNECT_TIMEOUT = 30

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style|head)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES_RE = re.compile(r"\n\s*\n+")
_LABEL_RE = re.compile(rb'X-GM-LABELS \((?P<labels>.*?)\)(?: |\))', re.DOTALL)
_UID_RE = re.compile(rb"UID (?P<uid>\d+)")


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def strip_html(raw: str) -> str:
    """Very small HTML to text: drop script/style/head, tags, unescape entities, collapse whitespace."""
    text = _SCRIPT_STYLE_RE.sub(" ", raw or "")
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", text, flags=re.IGNORECASE)
    text = _TAG_RE.sub(" ", text)
    text = html_lib.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def make_snippet(text: str | None, html: str | None, limit: int = SNIPPET_BYTES) -> str:
    """First `limit` bytes (UTF-8) of text/plain, falling back to stripped text/html."""
    body = (text or "").strip()
    if not body:
        body = strip_html(html or "")
    body = _WS_RE.sub(" ", body)
    body = _BLANK_LINES_RE.sub("\n", body).strip()
    encoded = body.encode("utf-8")
    if len(encoded) <= limit:
        return body
    return encoded[:limit].decode("utf-8", "ignore").rstrip()


def decode_header_value(raw: str | None) -> str:
    """Decode an RFC 2047 header (handles non-UTF8 encodings such as iso-8859-1)."""
    if not raw:
        return ""
    try:
        parts = decode_header(raw)
    except Exception:
        return str(raw)
    return "".join(decode_value(value, encoding) for value, encoding in parts).strip()


def _parse_date(msg: MailMessage) -> datetime | None:
    """UTC aware datetime from the Date header, None when missing or unparsable."""
    if not msg.date_str:
        return None
    parsed = msg.date
    if parsed.year <= 1900:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _addresses(msg: MailMessage, header: str) -> list[str]:
    values = msg.obj.get_all(header, [])
    decoded = [decode_header_value(v) for v in values]
    return [addr.lower() for _name, addr in getaddresses(decoded) if addr]


def normalize_message(msg: MailMessage, labels: list[str] | None = None, snippet_bytes: int = SNIPPET_BYTES) -> dict:
    """Reduce an imap-tools MailMessage to the columns stored on `emails`.

    Never includes attachments or full bodies. `date` is None when the message
    has no usable Date header; the caller substitutes the sync time.
    """
    from_name, from_email = "", ""
    if msg.from_values:
        from_name = (msg.from_values.name or "").strip()
        from_email = (msg.from_values.email or "").strip().lower()
    else:
        raw_from = decode_header_value(msg.obj.get("From"))
        pairs = getaddresses([raw_from]) if raw_from else []
        if pairs:
            from_name, from_email = pairs[0][0].strip(), pairs[0][1].strip().lower()

    message_id = (msg.obj.get("Message-ID") or msg.obj.get("Message-Id") or "").strip() or None
    references = msg.obj.get("In-Reply-To") or msg.obj.get("References") or ""
    thread_hint = references.strip().split()[0] if references.strip() else message_id

    return {
        "uid": int(msg.uid) if msg.uid is not None else None,
        "message_id": message_id,
        "thread_hint": thread_hint,
        "from_name": from_name,
        "from_email": from_email,
        "to_addrs": _addresses(msg, "To"),
        "subject": decode_header_value(msg.obj.get("Subject")) or "(no subject)",
        "date": _parse_date(msg),
        "snippet": make_snippet(msg.text, msg.html, snippet_bytes),
        "labels": list(labels or []),
        "has_attachments": any(part.get_filename() for part in msg.obj.walk()),
    }


def parse_gmail_labels(fetch_response: list) -> dict[int, list[str]]:
    """Parse `UID FETCH ... (X-GM-LABELS)` response lines into {uid: [labels]}."""
    out: dict[int, list[str]] = {}
    for item in fetch_response or []:
        line = item[0] if isinstance(item, tuple) else item
        if not isinstance(line, bytes):
            continue
        uid_match = _UID_RE.search(line)
        label_match = _LABEL_RE.search(line)
        if not uid_match:
            continue
        labels: list[str] = []
        if label_match:
            raw = label_match.group("labels").decode("utf-8", "ignore")
            for token in re.findall(r'"([^"]*)"|(\S+)', raw):
                value = token[0] or token[1]
                if value:
                    labels.append(value.replace("\\\\", "\\"))
        out[int(uid_match.group("uid"))] = labels
    return out


# ---------------------------------------------------------------------------
# Network layer
# ---------------------------------------------------------------------------

@contextmanager
def open_mailbox(email: str, password: str, host: str = DEFAULT_HOST, folder: str = "INBOX"):
    """Login and select the folder read-only from our side: we only ever SEARCH and FETCH."""
    box = MailBox(host, timeout=CONNECT_TIMEOUT)
    box.login(email, password, initial_folder=folder)
    try:
        yield box
    finally:
        try:
            box.logout()
        except Exception:
            pass


def test_login(email: str, password: str, host: str = DEFAULT_HOST) -> dict:
    """Connect, select INBOX, return a small status dict. Raises on failure."""
    with open_mailbox(email, password, host) as box:
        status = box.folder.status("INBOX", ["MESSAGES", "UIDNEXT"])
        return {"messages": int(status.get("MESSAGES", 0)), "uidnext": int(status.get("UIDNEXT", 0))}


def _fetch_labels(box: MailBox, uids: list[int]) -> dict[int, list[str]]:
    """Best effort Gmail labels via a raw UID FETCH (read-only). Returns {} on any problem."""
    if not uids:
        return {}
    try:
        uid_set = ",".join(str(u) for u in uids)
        typ, data = box.client.uid("FETCH", uid_set, "(X-GM-LABELS)")
        if typ != "OK":
            return {}
        return parse_gmail_labels(data)
    except Exception:
        return {}


def _search_uids(box: MailBox, last_uid: int | None, backfill_days: int) -> list[int]:
    if last_uid:
        # `n:*` always includes the highest UID even when it is <= n, so filter client-side.
        raw = box.uids(f"UID {int(last_uid) + 1}:*")
        return sorted(int(u) for u in raw if int(u) > int(last_uid))
    since = date.today() - timedelta(days=backfill_days)
    raw = box.uids(AND(date_gte=since))
    return sorted(int(u) for u in raw)


def fetch_new(
    email: str,
    password: str,
    *,
    last_uid: int | None,
    backfill_days: int = 7,
    host: str = DEFAULT_HOST,
    max_messages: int = 500,
    snippet_bytes: int = SNIPPET_BYTES,
) -> list[dict]:
    """Return normalized dicts for INBOX messages with UID > last_uid.

    On the first run (last_uid None) returns the last `backfill_days` days.
    Capped at `max_messages` oldest-first so a huge backlog is drained over
    several runs while last_uid still advances monotonically.
    """
    with open_mailbox(email, password, host) as box:
        uids = _search_uids(box, last_uid, backfill_days)[:max_messages]
        if not uids:
            return []
        labels = _fetch_labels(box, uids)
        out = []
        for msg in box.fetch(uid_list=[str(u) for u in uids], mark_seen=False, bulk=50):
            row = normalize_message(msg, labels.get(int(msg.uid), []), snippet_bytes)
            out.append(row)
        out.sort(key=lambda r: r["uid"] or 0)
        return out


def fetch_newest(email: str, password: str, n: int = 3, host: str = DEFAULT_HOST) -> list[dict]:
    """The `n` newest INBOX messages, headers only. Used by the smoke script."""
    with open_mailbox(email, password, host) as box:
        rows = []
        for msg in box.fetch("ALL", limit=n, reverse=True, mark_seen=False, headers_only=True, bulk=True):
            rows.append(normalize_message(msg))
        rows.sort(key=lambda r: r["uid"] or 0, reverse=True)
        return rows
