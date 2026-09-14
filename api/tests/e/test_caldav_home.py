from app.integrations.caldav_client import CalDAVClient


class _Principal:
    def __init__(self, client):
        self._client = client

    @property
    def calendar_home_set(self):
        self._client.url = "https://p55-caldav.icloud.com:443/1/calendars/"
        return "home"


class _FakeDav:
    def __init__(self):
        self.url = "https://caldav.icloud.com"
        self.calendar_calls = []

    def principal(self):
        return _Principal(self)

    def calendar(self, url):
        self.calendar_calls.append((self.url, url))
        return object()


def test_calendar_lookup_resolves_home_first():
    client = CalDAVClient.__new__(CalDAVClient)
    client._client = _FakeDav()
    client._principal = None
    client._calendar("https://p55-caldav.icloud.com:443/1/calendars/ABC/")
    client._calendar("https://p55-caldav.icloud.com:443/1/calendars/DEF/")
    assert [base for base, _ in client._client.calendar_calls] == ["https://p55-caldav.icloud.com:443/1/calendars/"] * 2
