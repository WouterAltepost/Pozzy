"""Manual smoke test against the real iCloud account. Not run by pytest.

Usage (from api/ with the venv active, root .env filled in):

    python scripts/caldav_smoke.py            # list calendars, next 5 events
    python scripts/caldav_smoke.py --write    # also create, read back and delete a test event
                                              # on the first calendar (or --calendar NAME)

Reads ICLOUD_USERNAME and ICLOUD_APP_PASSWORD (and optional ICLOUD_CALDAV_URL)
from the environment or the repo root .env.
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import load_root_dotenv  # noqa: E402
from app.integrations.caldav_client import (  # noqa: E402
    CalDAVError,
    build_ics,
    client_from_config,
    parse_occurrences,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="create, read back and delete a test event")
    parser.add_argument("--calendar", help="calendar name to use for --write (default: first)")
    parser.add_argument("--days", type=int, default=30, help="look-ahead window in days")
    args = parser.parse_args()

    load_root_dotenv()
    try:
        client = client_from_config(os.environ)
    except CalDAVError as exc:
        print(f"config error: {exc}")
        return 2

    print("Connecting to iCloud CalDAV as", os.environ.get("ICLOUD_USERNAME"))
    try:
        calendars = client.list_calendars()
    except CalDAVError as exc:
        print(f"FAILED to list calendars: {exc}")
        return 1
    print(f"\n{len(calendars)} calendars:")
    for cal in calendars:
        print(f"  - {cal['name']}\n      {cal['url']}")

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=args.days)
    occurrences = []
    print(f"\nFetching events between now and +{args.days}d ...")
    for cal in calendars:
        try:
            raws = client.fetch_events(cal["url"], now, window_end)
        except CalDAVError as exc:
            print(f"  ! {cal['name']}: {exc}")
            continue
        count = 0
        for raw in raws:
            try:
                for occ in parse_occurrences(raw.ics, now, window_end):
                    occurrences.append((cal["name"], occ, raw.etag))
                    count += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  ! {cal['name']}: could not parse {raw.href}: {exc}")
        print(f"  {cal['name']}: {len(raws)} objects, {count} occurrences")

    occurrences.sort(key=lambda item: item[1].start)
    print("\nNext 5 events:")
    for cal_name, occ, etag in occurrences[:5]:
        when = "all day " + occ.start.astimezone().strftime("%a %d %b") if occ.all_day else occ.start.astimezone().strftime("%a %d %b %H:%M") + occ.end.astimezone().strftime("-%H:%M")
        rec = f" (recurrence {occ.recurrence_id})" if occ.recurrence_id else ""
        print(f"  [{cal_name}] {when}  {occ.title}{rec}  etag={etag}")
    if not occurrences:
        print("  (none)")

    if not args.write:
        return 0

    target = None
    for cal in calendars:
        if args.calendar is None or cal["name"] == args.calendar:
            target = cal
            break
    if target is None:
        print(f"\nno calendar named {args.calendar!r}")
        return 1

    start = (now + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    uid, ics = build_ics(title="Pozzy smoke test (safe to delete)", start=start, end=start + timedelta(minutes=30), task_id="smoke")
    print(f"\nWriting test event to [{target['name']}] uid={uid}")
    href = client.create_event(target["url"], ics)
    print("  created", href)
    back = client.get_event(target["url"], uid)
    print("  read back:", "ok" if back and uid in back.ics else "NOT FOUND")
    deleted = client.delete_event(target["url"], uid)
    print("  deleted:", deleted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
