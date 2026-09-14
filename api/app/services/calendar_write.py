"""Calendar write access used when a task is scheduled.

TODO(stream B): replace with the real CalDAV write. Must set and return the
VEVENT UID so tasks.calendar_uid can be stored; return None when nothing was written.
"""


def create_event(task) -> str | None:
    """Create a calendar event for a scheduled task. No-op stub returns None."""
    return None


def update_event(task) -> bool:
    """Update the event linked via task.calendar_uid. No-op stub."""
    return False


def delete_event(task) -> bool:
    """Delete the event linked via task.calendar_uid. No-op stub."""
    return False
