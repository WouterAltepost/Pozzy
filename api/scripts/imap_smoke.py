"""Manual smoke test for the IMAP integration (stream C).

Connects to every account in MAIL_ACCOUNTS_JSON (repo root .env) and prints
the 3 newest INBOX subjects per account. Read-only. A failing account is
reported and the script continues with the next one.

Run from api/:  .venv/bin/python scripts/imap_smoke.py [--count 3]
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import load_root_dotenv  # noqa: E402
from app.integrations.imap_client import DEFAULT_HOST, fetch_newest, test_login  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()

    load_root_dotenv()
    raw = os.environ.get("MAIL_ACCOUNTS_JSON")
    if not raw:
        print("MAIL_ACCOUNTS_JSON is not set (expected in the repo root .env)")
        return 1
    try:
        accounts = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"MAIL_ACCOUNTS_JSON is not valid JSON: {exc}")
        return 1

    failures = 0
    for acc in accounts:
        label = acc.get("label") or acc.get("email") or "?"
        email = (acc.get("email") or "").strip()
        password = acc.get("password") or ""
        host = acc.get("imap_host") or DEFAULT_HOST
        print(f"\n== {label} <{email}> via {host}")
        if not email or not password:
            print("   skipped: email or password missing")
            failures += 1
            continue
        if "@" not in email or "." not in email.split("@", 1)[1]:
            print("   warning: address does not look complete (no dot in the domain)")
        try:
            status = test_login(email, password, host)
            print(f"   login ok, INBOX has {status['messages']} messages, UIDNEXT {status['uidnext']}")
            for row in fetch_newest(email, password, args.count, host):
                when = row["date"].isoformat() if row["date"] else "(no date)"
                sender = row["from_name"] or row["from_email"]
                print(f"   uid={row['uid']:<8} {when}  {sender[:30]:<30}  {row['subject'][:70]}")
        except Exception as exc:
            failures += 1
            print(f"   FAILED: {type(exc).__name__}: {exc}")

    print(f"\n{len(accounts) - failures}/{len(accounts)} accounts ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
