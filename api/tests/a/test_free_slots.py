from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.scheduling.free_slots import find_free_slots, rank_slots_deterministic

TZ = ZoneInfo("Europe/Amsterdam")
WINDOW = {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00", "timezone": "Europe/Amsterdam"}


def local(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=TZ)


# Monday 2026-09-14 06:00 local, before the working window opens.
MONDAY_EARLY = local(2026, 9, 14, 6)


def test_empty_calendar_fills_the_window():
    slots = find_free_slots([], [], WINDOW, 60, MONDAY_EARLY, days=1)
    assert len(slots) == 10
    assert slots[0]["start"] == local(2026, 9, 14, 8)
    assert slots[-1]["end"] == local(2026, 9, 14, 18)
    assert "morning" in slots[0]["reason_hints"] and "empty_day" in slots[0]["reason_hints"]


def test_fully_booked_day_yields_nothing():
    events = [(local(2026, 9, 14, 8), local(2026, 9, 14, 18))]
    assert find_free_slots(events, [], WINDOW, 30, MONDAY_EARLY, days=1) == []


def test_task_longer_than_any_gap():
    events = [(local(2026, 9, 14, 10), local(2026, 9, 14, 11)), (local(2026, 9, 14, 13), local(2026, 9, 14, 17))]
    # Gaps: 08-10 (2h), 11-13 (2h), 17-18 (1h). A 3h task fits nowhere.
    assert find_free_slots(events, [], WINDOW, 180, MONDAY_EARLY, days=1) == []
    # A 2h task fits exactly twice.
    slots = find_free_slots(events, [], WINDOW, 120, MONDAY_EARLY, days=1)
    assert [(s["start"].hour, s["end"].hour) for s in slots] == [(8, 10), (11, 13)]


def test_weekend_excluded():
    friday = local(2026, 9, 18, 6)
    slots = find_free_slots([], [], WINDOW, 600, friday, days=4)  # Fri, Sat, Sun, Mon
    days = sorted({s["start"].date() for s in slots})
    assert days == [date(2026, 9, 18), date(2026, 9, 21)]


def test_window_crossing_dst_change():
    # Clocks go back on Sunday 2026-10-25 in Europe/Amsterdam. Monday 26 Oct must still open at 08:00 local.
    friday = local(2026, 10, 23, 6)
    slots = find_free_slots([], [], WINDOW, 600, friday, days=4)
    by_day = {s["start"].date(): s for s in slots}
    monday = by_day[date(2026, 10, 26)]
    assert monday["start"].hour == 8 and monday["end"].hour == 18
    assert monday["start"].utcoffset() == timedelta(hours=1)
    assert by_day[date(2026, 10, 23)]["start"].utcoffset() == timedelta(hours=2)
    # Event given in UTC on the DST day still blocks the right local hours.
    utc_event = (datetime(2026, 10, 26, 7, 0, tzinfo=ZoneInfo("UTC")), datetime(2026, 10, 26, 9, 0, tzinfo=ZoneInfo("UTC")))
    slots = find_free_slots([utc_event], [], WINDOW, 60, local(2026, 10, 26, 6), days=1)
    assert slots[0]["start"] == local(2026, 10, 26, 10)


def test_from_dt_in_the_middle_of_a_day_skips_the_past_and_aligns():
    now = local(2026, 9, 14, 10, 7)
    slots = find_free_slots([], [], WINDOW, 60, now, days=1)
    assert slots[0]["start"] == local(2026, 9, 14, 10, 15)


def test_scheduled_tasks_and_overlapping_events_are_merged():
    events = [(local(2026, 9, 14, 9), local(2026, 9, 14, 10, 30)), (local(2026, 9, 14, 10), local(2026, 9, 14, 11))]
    tasks = [(local(2026, 9, 14, 10, 45), local(2026, 9, 14, 12))]
    slots = find_free_slots(events, tasks, WINDOW, 60, MONDAY_EARLY, days=1)
    starts = [s["start"].hour for s in slots]
    assert starts == [8, 12, 13, 14, 15, 16, 17]


def test_events_outside_window_are_ignored_and_partial_overlap_clipped():
    events = [(local(2026, 9, 14, 6), local(2026, 9, 14, 8, 30)), (local(2026, 9, 14, 17, 30), local(2026, 9, 14, 20))]
    slots = find_free_slots([], [], WINDOW, 30, MONDAY_EARLY, days=1)
    assert len(slots) == 20
    slots = find_free_slots(events, [], WINDOW, 30, MONDAY_EARLY, days=1)
    assert slots[0]["start"] == local(2026, 9, 14, 8, 30)
    assert slots[-1]["end"] == local(2026, 9, 14, 17, 30)


def test_custom_window_and_days():
    window = {"days": [6, 7], "start": "10:00", "end": "12:00"}
    slots = find_free_slots([], [], window, 60, MONDAY_EARLY, days=7)
    assert {s["start"].date() for s in slots} == {date(2026, 9, 19), date(2026, 9, 20)}
    assert all(s["start"].hour in (10, 11) for s in slots)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        find_free_slots([], [], WINDOW, 0, MONDAY_EARLY)
    with pytest.raises(ValueError):
        find_free_slots([], [], WINDOW, 30, datetime(2026, 9, 14, 6))


def test_deterministic_ranking_prefers_due_side_mornings_and_spreads_days():
    slots = find_free_slots([], [], WINDOW, 60, MONDAY_EARLY, days=7)
    top = rank_slots_deterministic(slots, due_date=date(2026, 9, 16), limit=3)
    assert [s["start"].date() for s in top] == [date(2026, 9, 14), date(2026, 9, 15), date(2026, 9, 16)]
    assert all(s["start"].hour == 8 for s in top)

    # Only Thursday and Friday are free within 7 days: one slot each first, then a second Thursday slot fills the third spot.
    booked = [(local(2026, 9, d, 8), local(2026, 9, d, 18)) for d in (14, 15, 16)]
    top = rank_slots_deterministic(find_free_slots(booked, [], WINDOW, 60, MONDAY_EARLY, days=7), due_date=date(2026, 9, 18))
    assert [s["start"].date() for s in top] == [date(2026, 9, 17), date(2026, 9, 18), date(2026, 9, 17)]
    assert top[2]["start"].hour == 9

    # Slots after the due date rank below slots before it, even when they are earlier in the week order.
    late = rank_slots_deterministic(find_free_slots([], [], WINDOW, 60, MONDAY_EARLY, days=7), due_date=date(2026, 9, 14), limit=2)
    assert [s["start"].date() for s in late] == [date(2026, 9, 14), date(2026, 9, 15)]
