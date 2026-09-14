from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.integrations.caldav_client import build_ics, parse_occurrences

from .conftest import load_ics

AMS = ZoneInfo("Europe/Amsterdam")
WINDOW = (datetime(2026, 9, 7, tzinfo=timezone.utc), datetime(2026, 11, 8, tzinfo=timezone.utc))


def test_single_event_is_utc_and_not_recurring():
    [occ] = parse_occurrences(load_ics("single.ics"), *WINDOW)
    assert occ.uid == "single-1"
    assert occ.recurrence_id is None
    assert occ.start == datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)  # 14:00 CEST
    assert occ.end == datetime(2026, 9, 15, 12, 30, tzinfo=timezone.utc)
    assert occ.all_day is False
    assert occ.title == "Pillen bellen"
    assert occ.location == "Home"
    assert occ.description == "Call the pharmacy"
    assert occ.task_id is None


def test_all_day_event_spans_local_day():
    [occ] = parse_occurrences(load_ics("allday.ics"), *WINDOW)
    assert occ.all_day is True
    assert occ.start == datetime(2026, 9, 18, tzinfo=AMS).astimezone(timezone.utc)
    assert occ.end == datetime(2026, 9, 19, tzinfo=AMS).astimezone(timezone.utc)
    assert occ.recurrence_id is None


def test_weekly_with_exdate_and_moved_override():
    occs = parse_occurrences(load_ics("weekly.ics"), datetime(2026, 9, 1, tzinfo=timezone.utc), datetime(2026, 10, 6, tzinfo=timezone.utc))
    starts = [o.start.astimezone(AMS).strftime("%d %H:%M") for o in occs]
    # 7 Sep, 14 Sep moved to 14:00, 21 Sep excluded, 28 Sep, 5 Oct
    assert starts == ["07 10:00", "14 14:00", "28 10:00", "05 10:00"]
    moved = occs[1]
    assert moved.title == "Standup (moved)"
    assert moved.recurrence_id == "2026-09-14T08:00:00+00:00"  # original occurrence start, stable key
    assert all(o.recurrence_id for o in occs)
    assert len({o.recurrence_id for o in occs}) == len(occs)


def test_recurrence_across_dst_change_keeps_local_hour():
    occs = parse_occurrences(load_ics("dst.ics"), *WINDOW)
    assert [o.start.astimezone(AMS).hour for o in occs] == [10, 10, 10]
    # 19 Oct is CEST (UTC+2), 26 Oct and 2 Nov are CET (UTC+1)
    assert [o.start.hour for o in occs] == [8, 9, 9]


def test_duration_without_dtend():
    [occ] = parse_occurrences(load_ics("duration.ics"), *WINDOW)
    assert occ.end - occ.start == timedelta(minutes=45)


def test_window_filters_occurrences():
    occs = parse_occurrences(load_ics("dst.ics"), datetime(2026, 10, 25, tzinfo=timezone.utc), datetime(2026, 10, 27, tzinfo=timezone.utc))
    assert len(occs) == 1
    assert occs[0].start.astimezone(AMS).day == 26


def test_build_ics_round_trips_task_id_and_times():
    start = datetime(2026, 9, 16, 9, 0, tzinfo=AMS)
    uid, ics = build_ics(title="Write report", start=start, end=start + timedelta(hours=2), task_id="8f6b7a1e-1111-2222-3333-444444444444", description="desc")
    assert "X-POZZY-TASK-ID:8f6b7a1e-1111-2222-3333-444444444444" in ics
    assert "DTSTART:20260916T070000Z" in ics
    [occ] = parse_occurrences(ics, *WINDOW)
    assert occ.uid == uid
    assert occ.task_id == "8f6b7a1e-1111-2222-3333-444444444444"
    assert occ.start == start.astimezone(timezone.utc)
    assert occ.recurrence_id is None


def test_build_ics_all_day_uses_dates():
    start = datetime(2026, 9, 16, tzinfo=AMS)
    _, ics = build_ics(title="Day off", start=start, end=start + timedelta(days=1), all_day=True)
    assert "DTSTART;VALUE=DATE:20260916" in ics
    assert "DTEND;VALUE=DATE:20260917" in ics
    [occ] = parse_occurrences(ics, *WINDOW)
    assert occ.all_day is True
