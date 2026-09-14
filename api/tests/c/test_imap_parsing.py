from datetime import timezone

from imap_tools import MailMessage

from app.integrations.imap_client import make_snippet, normalize_message, parse_gmail_labels, strip_html
from tests.c.conftest import RAW_HTML_ONLY, RAW_LATIN1_SUBJECT, RAW_MULTIPART, RAW_NO_DATE


def _norm(raw, labels=None):
    return normalize_message(MailMessage.from_bytes(raw), labels)


def test_multipart_prefers_text_plain_and_flags_attachment_without_storing_it():
    row = _norm(RAW_MULTIPART)
    assert row["from_name"] == "Alice Example"
    assert row["from_email"] == "alice@client.com"
    assert row["to_addrs"] == ["wout@example.com"]
    assert row["subject"] == "Invoice question"
    assert row["message_id"] == "<multi-1@client.com>"
    assert row["snippet"].startswith("Hi Wout,")
    assert "invoice for August" in row["snippet"]
    assert "<b>" not in row["snippet"]
    assert "JVBERi" not in row["snippet"]
    assert row["has_attachments"] is True
    assert row["date"].tzinfo is timezone.utc
    assert row["date"].isoformat() == "2026-09-14T08:15:00+00:00"


def test_html_only_falls_back_to_stripped_html():
    row = _norm(RAW_HTML_ONLY)
    assert row["from_name"] == "Shop"
    assert "Shipped!" in row["snippet"]
    assert "Your order & tracking:" in row["snippet"]
    assert "NL123" in row["snippet"]
    assert "<" not in row["snippet"]
    assert "alert" not in row["snippet"]
    assert "color:red" not in row["snippet"]


def test_non_utf8_subject_and_body_are_decoded():
    row = _norm(RAW_LATIN1_SUBJECT)
    assert row["subject"] == "Prüfung nächste Woche"
    assert row["from_name"] == "Jörg Müller"
    assert "Prüfung ist nächste Woche" in row["snippet"]


def test_missing_date_header_yields_none():
    row = _norm(RAW_NO_DATE)
    assert row["date"] is None
    assert row["subject"] == "Statement ready"
    assert row["from_email"] == "bank@finance.example"
    assert row["from_name"] == ""


def test_labels_are_attached_when_given():
    row = _norm(RAW_HTML_ONLY, ["\\Inbox", "Shopping"])
    assert row["labels"] == ["\\Inbox", "Shopping"]


def test_snippet_is_capped_at_2kb_on_a_utf8_boundary():
    text = "é" * 3000  # 2 bytes each
    snippet = make_snippet(text, None)
    assert len(snippet.encode("utf-8")) <= 2048
    assert snippet == "é" * 1024


def test_snippet_collapses_whitespace():
    assert make_snippet("a    b\n\n\n\nc", None) == "a b\nc"


def test_strip_html_keeps_line_breaks_for_blocks():
    assert strip_html("<p>one</p><p>two<br>three</p>") == "one\ntwo\nthree"


def test_parse_gmail_labels_response():
    data = [b'12 (X-GM-LABELS (\\Inbox "\\\\Important" "Project X") UID 55)', b')', None]
    assert parse_gmail_labels(data) == {55: ["\\Inbox", "\\Important", "Project X"]}
    assert parse_gmail_labels([]) == {}
