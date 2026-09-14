"""Stream B fixtures: a fake CalDAV client serving recorded ICS files, no network."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.integrations.caldav_client import CalDAVError, RawEvent
from app.modules.calendar import service
from conftest import bearer

FIXTURES = Path(__file__).parent / "fixtures"
CAL_A = "https://caldav.example/cal/A/"
CAL_B = "https://caldav.example/cal/B/"
CALENDARS = [{"name": "Taken", "url": CAL_A}, {"name": "Uni", "url": CAL_B}]

# Frozen "now": Monday 14 Sep 2026 09:00 Amsterdam (07:00 UTC). Sync window is 7 Sep to 14 Oct.
NOW = datetime(2026, 9, 14, 7, 0, tzinfo=timezone.utc)


def load_ics(name: str) -> str:
    return (FIXTURES / name).read_text()


class FakeCalDAVClient:
    """Serves {calendar_url: [RawEvent]} and records writes. Set `failing` to raise on fetch."""

    def __init__(self):
        self.calendars = list(CALENDARS)
        self.objects: dict[str, list[RawEvent]] = {CAL_A: [], CAL_B: []}
        self.failing: set[str] = set()
        self.created: list[tuple[str, str]] = []
        self.updated: list[tuple[str, str, str]] = []
        self.deleted: list[tuple[str, str]] = []
        self.fetch_calls = 0

    def put(self, calendar_url: str, uid_file: str, etag: str = "e1", href: str | None = None):
        ics = load_ics(uid_file) if uid_file.endswith(".ics") else uid_file
        href = href or f"{calendar_url}{uid_file}"
        self.objects.setdefault(calendar_url, [])
        self.objects[calendar_url] = [o for o in self.objects[calendar_url] if o.href != href]
        self.objects[calendar_url].append(RawEvent(href=href, etag=etag, ics=ics))

    def remove(self, calendar_url: str, uid_file: str):
        href = f"{calendar_url}{uid_file}"
        self.objects[calendar_url] = [o for o in self.objects[calendar_url] if o.href != href]

    # CalDAVClient interface
    def list_calendars(self):
        return list(self.calendars)

    def fetch_events(self, calendar_url, start, end):
        self.fetch_calls += 1
        if calendar_url in self.failing:
            raise CalDAVError("fetch_events: DAVError: 503")
        return list(self.objects.get(calendar_url, []))

    def get_event(self, calendar_url, uid):
        for obj in self.objects.get(calendar_url, []):
            if f"UID:{uid}" in obj.ics:
                return obj
        return None

    def create_event(self, calendar_url, ics_text):
        if calendar_url in self.failing:
            raise CalDAVError("create_event: DAVError: 503")
        self.created.append((calendar_url, ics_text))
        href = f"{calendar_url}created-{len(self.created)}.ics"
        self.objects.setdefault(calendar_url, []).append(RawEvent(href=href, etag=f"c{len(self.created)}", ics=ics_text))
        return href

    def update_event(self, calendar_url, uid, ics_text):
        if calendar_url in self.failing:
            raise CalDAVError("update_event: DAVError: 503")
        self.updated.append((calendar_url, uid, ics_text))
        objs = self.objects.setdefault(calendar_url, [])
        for i, obj in enumerate(objs):
            if f"UID:{uid}" in obj.ics:
                objs[i] = RawEvent(href=obj.href, etag=f"u{len(self.updated)}", ics=ics_text)
                return obj.href
        raise CalDAVError(f"update_event: NotFoundError: {uid}")

    def delete_event(self, calendar_url, uid):
        if calendar_url in self.failing:
            raise CalDAVError("delete_event: DAVError: 503")
        self.deleted.append((calendar_url, uid))
        objs = self.objects.setdefault(calendar_url, [])
        before = len(objs)
        self.objects[calendar_url] = [o for o in objs if f"UID:{uid}" not in o.ics]
        return len(self.objects[calendar_url]) < before


@pytest.fixture
def fake_client(app, monkeypatch):
    client = FakeCalDAVClient()
    monkeypatch.setattr(service, "client_factory", lambda account: client)
    monkeypatch.setitem(app.config, "ICLOUD_USERNAME", "wout@icloud.test")
    monkeypatch.setitem(app.config, "ICLOUD_APP_PASSWORD", "secret")
    return client


@pytest.fixture
def headers(token_factory):
    return bearer(token_factory())
