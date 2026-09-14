"""Anthropic client. Owned by stream D.

Wave 1 stub: every function returns None, meaning "no AI answer, use the
deterministic fallback". Signatures and JSON shapes are in docs/AI_CONTRACTS.md.
Callers must treat None and exceptions as "fall back" so pages never depend
on this module (CLAUDE.md rule 1).

TODO(stream D): implement, log to ai_calls, honour Settings ai_enabled.<feature>.
"""


def rank_slots(task: dict, candidates: list[dict], context: dict | None = None) -> list[dict] | None:
    """Rank candidate slots for a task. See AI_CONTRACTS.md 'rank_slots'."""
    return None


def suggest_dos(candidates: dict, context: dict | None = None) -> list[dict] | None:
    """Pick three do's from tasks and deadlines. See AI_CONTRACTS.md 'suggest_dos'."""
    return None
