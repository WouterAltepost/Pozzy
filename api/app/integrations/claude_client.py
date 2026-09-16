"""Anthropic client. Owned by stream D.

Every Claude call in Pozzy goes through `_call` (CLAUDE.md rule 6):

1. checks the feature kill switch in Settings `ai_enabled.<switch>`,
2. resolves the model from CLAUDE_MODEL_FAST or CLAUDE_MODEL_SMART,
3. renders a named prompt template from app/prompts/<name>.md
   (docs/prompts/<name>.md links to the same file),
4. sends one messages.create request,
5. parses the reply as JSON and validates it with a pydantic schema,
6. writes one `ai_calls` row with tokens and an estimated cost,
7. returns the validated object, or None on any failure.

`_call` never raises. Callers treat None as "use the deterministic fallback"
(docs/AI_CONTRACTS.md). Public contract functions keep the signatures that
streams A, B and C call; their JSON shapes are in docs/AI_CONTRACTS.md.
"""
import json
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from flask import current_app, has_app_context
from pydantic import BaseModel

from ..extensions import db
from ..models import AiCall
from ..settings_defaults import DEFAULTS, get_setting

log = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
CLIENT_EXTENSION_KEY = "pozzy_anthropic"

# USD per million tokens: input, output, cache write (5 min TTL), cache read.
# Update when Anthropic changes prices; the smoke script prints the row it used.
PRICES: dict[str, dict[str, Decimal]] = {
    "claude-haiku-4-5": {"input": Decimal("1.00"), "output": Decimal("5.00"), "cache_write": Decimal("1.25"), "cache_read": Decimal("0.10")},
    "claude-sonnet-4-5": {"input": Decimal("3.00"), "output": Decimal("15.00"), "cache_write": Decimal("3.75"), "cache_read": Decimal("0.30")},
    "claude-sonnet-5": {"input": Decimal("2.00"), "output": Decimal("10.00"), "cache_write": Decimal("2.50"), "cache_read": Decimal("0.20")},
    "claude-opus-5": {"input": Decimal("5.00"), "output": Decimal("25.00"), "cache_write": Decimal("6.25"), "cache_read": Decimal("0.50")},
}
PRICE_ALIASES = {
    "claude-haiku-4-5-20251001": "claude-haiku-4-5",
    "claude-sonnet-4-5-20250929": "claude-sonnet-4-5",
}
MILLION = Decimal(1_000_000)

TIER_CONFIG_KEY = {"fast": "CLAUDE_MODEL_FAST", "smart": "CLAUDE_MODEL_SMART"}


class ClaudeCallError(Exception):
    """Internal: any failure between request and validated answer."""


# --- kill switch, pricing, prompts -------------------------------------------


def ai_is_enabled(switch: str | None) -> bool:
    """True when Settings ai_enabled.<switch> is on. Missing keys fall back to the defaults."""
    if switch is None:
        return True
    stored = get_setting("ai_enabled") or {}
    merged = {**DEFAULTS.get("ai_enabled", {}), **(stored if isinstance(stored, dict) else {})}
    return bool(merged.get(switch, True))


def price_row(model: str) -> dict[str, Decimal] | None:
    return PRICES.get(PRICE_ALIASES.get(model, model))


def estimate_cost(model: str, input_tokens: int = 0, output_tokens: int = 0, cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> Decimal:
    """Estimated USD for one call. Unknown models cost 0 and log a warning so spend is never silently wrong."""
    row = price_row(model)
    if row is None:
        log.warning("claude_client: no price for model %s, logging cost 0", model)
        return Decimal("0")
    total = (
        Decimal(input_tokens) * row["input"]
        + Decimal(output_tokens) * row["output"]
        + Decimal(cache_write_tokens) * row["cache_write"]
        + Decimal(cache_read_tokens) * row["cache_read"]
    ) / MILLION
    return total.quantize(Decimal("0.000001"))


_prompt_cache: dict[str, dict[str, str]] = {}


def load_prompt(name: str) -> dict[str, str]:
    """Parse app/prompts/<name>.md into its `## System` and `## User` sections."""
    if name in _prompt_cache:
        return _prompt_cache[name]
    path = PROMPTS_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().lower()
            buf = []
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    if "system" not in sections or "user" not in sections:
        raise ClaudeCallError(f"prompt {name} needs '## System' and '## User' sections")
    _prompt_cache[name] = sections
    return sections


def render_user(template: str, payload: dict) -> str:
    """Fill `{{json}}` with the whole payload and `{{key}}` with top-level scalar keys."""
    out = template.replace("{{json}}", json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    for key, value in payload.items():
        if isinstance(value, (str, int, float)):
            out = out.replace("{{" + key + "}}", str(value))
    return out


# --- client and the single call helper -----------------------------------------


def get_client():
    """Lazily built Anthropic client, one per process. None when no API key is configured.

    Tests inject a fake under app.extensions[CLIENT_EXTENSION_KEY].
    """
    ext = current_app.extensions
    if CLIENT_EXTENSION_KEY in ext:
        return ext[CLIENT_EXTENSION_KEY]
    key = current_app.config.get("ANTHROPIC_API_KEY")
    if current_app.config.get("TESTING") or not key:
        # pytest never reaches the network; tests inject a fake client explicitly.
        ext[CLIENT_EXTENSION_KEY] = None
        return None
    import anthropic

    ext[CLIENT_EXTENSION_KEY] = anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=2)
    return ext[CLIENT_EXTENSION_KEY]


def model_for(tier: str) -> str:
    return current_app.config[TIER_CONFIG_KEY[tier]]


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def extract_json(text: str) -> Any:
    """Parse the model's reply as JSON, tolerating code fences and prose around one JSON value."""
    cleaned = _FENCE.sub("", text.strip()).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    starts = [i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1]
    if not starts:
        raise ClaudeCallError("reply contains no JSON")
    start = min(starts)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if end <= start:
        raise ClaudeCallError("reply contains no JSON")
    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ClaudeCallError(f"reply is not valid JSON: {exc}") from exc


def _log_call(feature: str, model: str, usage: dict, ok: bool, error: str | None) -> AiCall | None:
    """Write one ai_calls row. Commits the session. Never raises."""
    row = AiCall(
        feature=feature,
        model=model,
        input_tokens=usage.get("input_tokens", 0) + usage.get("cache_write_tokens", 0) + usage.get("cache_read_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cost_estimate=estimate_cost(model, usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("cache_write_tokens", 0), usage.get("cache_read_tokens", 0)),
        ok=ok,
        error=(error or None) and str(error)[:2000],
    )
    try:
        db.session.add(row)
        db.session.commit()
        return row
    except Exception:
        db.session.rollback()
        log.exception("claude_client: could not write ai_calls row for %s", feature)
        return None


def _usage_dict(response) -> dict:
    usage = getattr(response, "usage", None)
    return {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_write_tokens": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
        "cache_read_tokens": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
    }


def standing_rules_block() -> str:
    """Wouter's rules and context from Settings, rendered for every system prompt.
    Rules outrank the feature instructions; the block is empty when he wrote none."""
    try:
        from ..settings_defaults import get_setting

        rules = [str(r).strip() for r in (get_setting("ai_rules") or []) if str(r).strip()]
        context = str(get_setting("ai_context") or "").strip()
    except Exception:
        log.exception("claude_client: could not read ai_rules")
        return ""
    if not rules and not context:
        return ""
    parts = []
    if rules:
        parts.append("## Standing rules from the user\nThese are hard constraints. They win over every instruction that follows, including preferences about mornings, spreading work or focus time. When a rule leaves no acceptable choice, leave the item out and say which rule.\n" + "\n".join(f"- {r}" for r in rules[:40]))
    if context:
        parts.append("## About the user\n" + context[:2000])
    return "\n\n".join(parts) + "\n\n## Task instructions\n"


def standing_rules_list() -> list[str]:
    """The rules alone, for features that want to repeat them next to the data."""
    try:
        from ..settings_defaults import get_setting

        return [str(r).strip() for r in (get_setting("ai_rules") or []) if str(r).strip()][:40]
    except Exception:
        return []


def _call(
    *,
    feature: str,
    switch: str | None,
    tier: str,
    prompt: str,
    payload: dict,
    schema: type[BaseModel],
    max_tokens: int = 1024,
    cache_system: bool = False,
) -> BaseModel | None:
    """The one path to Anthropic. Returns a validated `schema` instance or None. Never raises."""
    if not has_app_context():
        log.error("claude_client._call used outside an app context")
        return None
    try:
        if not ai_is_enabled(switch):
            log.info("claude_client: %s skipped, ai_enabled.%s is off", feature, switch)
            return None
    except Exception:
        log.exception("claude_client: could not read kill switch, treating as off")
        return None

    model = "unknown"
    usage: dict = {}
    try:
        model = model_for(tier)
        client = get_client()
        if client is None:
            raise ClaudeCallError("ANTHROPIC_API_KEY is not set")
        sections = load_prompt(prompt)
        system_block: dict = {"type": "text", "text": standing_rules_block() + sections["system"]}
        if cache_system:
            system_block["cache_control"] = {"type": "ephemeral"}
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[system_block],
            messages=[{"role": "user", "content": render_user(sections["user"], payload)}],
        )
        usage = _usage_dict(response)
        stop = getattr(response, "stop_reason", None)
        if stop == "max_tokens":
            raise ClaudeCallError(f"reply truncated at max_tokens={max_tokens}")
        if stop == "refusal":
            raise ClaudeCallError("model refused the request")
        text = "".join(getattr(block, "text", "") for block in (response.content or []) if getattr(block, "type", "") == "text")
        if not text.strip():
            raise ClaudeCallError("empty reply")
        data = extract_json(text)
        result = schema.model_validate(data)
    except Exception as exc:  # any failure: log it, fall back
        message = f"{type(exc).__name__}: {exc}"
        log.warning("claude_client: %s failed: %s", feature, message[:300])
        _log_call(feature, model, usage, ok=False, error=message)
        return None

    _log_call(feature, model, usage, ok=True, error=None)
    return result


# --- smoke ----------------------------------------------------------------------


class PingAnswer(BaseModel):
    ok: bool
    message: str


def ping(note: str = "hello") -> dict | None:
    """One cheap fast-model call for api/scripts/claude_smoke.py. Not tied to a kill switch."""
    answer = _call(feature="smoke", switch=None, tier="fast", prompt="ping", payload={"note": note}, schema=PingAnswer, max_tokens=128)
    return answer.model_dump() if answer else None


# --- contracts (docs/AI_CONTRACTS.md) --------------------------------------------


class _RankedSlot(BaseModel):
    start: str
    end: str
    reason: str = ""


class RankSlotsAnswer(BaseModel):
    slots: list[_RankedSlot]


def rank_slots(task: dict, candidates: list[dict], context: dict | None = None) -> list[dict] | None:
    """Rank candidate slots for a task. See AI_CONTRACTS.md 'rank_slots'."""
    if not candidates:
        return None
    limit = int((context or {}).get("limit") or 3)
    payload = {"task": task, "candidates": candidates[:12], "limit": limit}
    answer = _call(feature="rank_slots", switch="scheduling", tier="smart", prompt="rank_slots", payload=payload, schema=RankSlotsAnswer, max_tokens=600)
    if answer is None:
        return None
    allowed = {(c["start"], c["end"]) for c in candidates}
    out, seen = [], set()
    for slot in answer.slots:
        key = (slot.start, slot.end)
        if key in allowed and key not in seen:
            seen.add(key)
            out.append({"start": slot.start, "end": slot.end, "reason": slot.reason.strip()[:300]})
        if len(out) >= limit:
            break
    return out or None


class _SuggestedDo(BaseModel):
    title: str
    task_id: str | None = None
    reason: str = ""


class SuggestDosAnswer(BaseModel):
    dos: list[_SuggestedDo]


def suggest_dos(candidates: dict, context: dict | None = None) -> list[dict] | None:
    """Pick three do's from tasks and deadlines. See AI_CONTRACTS.md 'suggest_dos'."""
    count = int((context or {}).get("count") or 3)
    payload = {**candidates, "count": count}
    answer = _call(feature="suggest_dos", switch="three_dos", tier="smart", prompt="suggest_dos", payload=payload, schema=SuggestDosAnswer, max_tokens=600)
    if answer is None:
        return None
    allowed_ids = {t.get("id") for t in candidates.get("tasks", [])} | {d.get("task_id") for d in candidates.get("deadlines", []) if d.get("task_id")}
    out = []
    for item in answer.dos:
        title = item.title.strip()
        if not title:
            continue
        task_id = item.task_id if item.task_id in allowed_ids else None
        out.append({"title": title[:200], "task_id": task_id, "reason": item.reason.strip()[:300]})
        if len(out) >= count:
            break
    return out or None


# --- stream D's own features -------------------------------------------------------


def parse_capture(payload: dict) -> dict | None:
    """Propose what a quick-capture line is. See docs/AI_CONTRACTS.md 'parse_capture'."""
    from ..modules.captures.schemas import CaptureProposal

    answer = _call(feature="capture_parse", switch="capture", tier="smart", prompt="capture_parse", payload=payload, schema=CaptureProposal, max_tokens=700)
    return answer.model_dump() if answer else None


class BriefingAnswer(BaseModel):
    text: str


def write_briefing(context: dict) -> str | None:
    """Morning briefing text from a context dict. See docs/AI_CONTRACTS.md 'write_briefing'."""
    answer = _call(feature="daily_briefing", switch="briefing", tier="smart", prompt="daily_briefing", payload=context, schema=BriefingAnswer, max_tokens=900)
    text = (answer.text or "").strip() if answer else ""
    return text or None


class _BriefingAction(BaseModel):
    type: str
    email_id: str | None = None
    task_id: str | None = None
    title: str | None = None
    body: str | None = None
    area: str | None = None
    hours: float | None = None
    reason: str = ""


class BriefingReplyAnswer(BaseModel):
    reply: str
    text: str
    actions: list[_BriefingAction] = []


def reply_briefing(payload: dict) -> dict | None:
    """Reply to a note on the briefing: acknowledgement, rewritten briefing, proposed actions.
    See docs/AI_CONTRACTS.md 'reply_briefing'. Ids are validated by the caller against the candidates."""
    answer = _call(feature="briefing_reply", switch="briefing", tier="smart", prompt="briefing_reply", payload=payload, schema=BriefingReplyAnswer, max_tokens=1400)
    if answer is None or not answer.text.strip():
        return None
    return {"reply": answer.reply.strip(), "text": answer.text.strip(), "actions": [a.model_dump() for a in answer.actions[:6]]}


class _PlanCheck(BaseModel):
    option: int
    needs_before: int = 0
    needs_after: int = 0


class _PlanPick(BaseModel):
    id: str
    place: bool = True
    option: int = 0
    checks: list[_PlanCheck] = []
    rule_check: str = ""
    reason: str = ""


class PlanAnswer(BaseModel):
    items: list[_PlanPick] = []


def plan_week(payload: dict) -> dict | None:
    """Pick one offered option per plan item. Returns {item_id: {option, reason}} or None.
    See docs/AI_CONTRACTS.md 'plan_week'. The caller validates option indexes and overlaps."""
    answer = _call(feature="plan_week", switch="scheduling", tier="smart", prompt="plan_week", payload=payload, schema=PlanAnswer, max_tokens=1200)
    if answer is None:
        return None
    return {
        p.id: {
            "option": p.option if p.place else -1,
            "place": p.place,
            "reason": p.reason.strip(),
            "checks": {c.option: (max(0, c.needs_before), max(0, c.needs_after)) for c in p.checks},
        }
        for p in answer.items
    }


class _FocusItem(BaseModel):
    title: str
    area: str | None = None
    target_value: float | None = None
    task_id: str | None = None
    reason: str = ""


class WeeklyReviewAnswer(BaseModel):
    reflection: str
    next_week_focus: list[_FocusItem] = []


def review_week(stats: dict, max_goals: int = 5) -> dict | None:
    """Reflection text plus next week's goal draft from a stats snapshot. See docs/AI_CONTRACTS.md 'review_week'."""
    payload = {**stats, "max_goals": max_goals}
    answer = _call(feature="weekly_review", switch="weekly_review", tier="smart", prompt="weekly_review", payload=payload, schema=WeeklyReviewAnswer, max_tokens=1400)
    if answer is None or not answer.reflection.strip():
        return None
    allowed = {c.get("id") for c in stats.get("open_task_candidates", [])} | {d.get("task_id") for d in (stats.get("deadlines") or {}).get("upcoming", []) if d.get("task_id")}
    focus = []
    for item in answer.next_week_focus:
        title = item.title.strip()
        if not title:
            continue
        focus.append(
            {
                "title": title[:200],
                "area": item.area.strip() if item.area else None,
                "target_value": item.target_value,
                "task_id": item.task_id if item.task_id in allowed else None,
                "reason": item.reason.strip()[:300],
            }
        )
        if len(focus) >= max_goals:
            break
    return {"reflection": answer.reflection.strip(), "next_week_focus": focus}


# --- stream C's contract ---------------------------------------------------------

EMAIL_CATEGORIES = ("client", "school", "finance", "personal", "newsletter", "notification", "other")
AREA_NAMES = ("Study", "Work", "Personal", "Health")
DEFAULT_MAIL_BATCH = 15


class _EmailResult(BaseModel):
    id: str
    priority: int
    category: str
    area: str | None = None
    needs_reply: bool = False
    one_line_summary: str = ""


class ClassifyEmailsAnswer(BaseModel):
    results: list[_EmailResult]


def _clean_email_result(item: _EmailResult, allowed_ids: set[str]) -> dict | None:
    if item.id not in allowed_ids or item.priority not in (1, 2, 3, 4):
        return None
    category = item.category.strip().lower()
    if category not in EMAIL_CATEGORIES:
        return None
    summary = item.one_line_summary.strip()
    if not summary:
        return None
    area = item.area.strip().capitalize() if item.area else None
    return {
        "id": item.id,
        "priority": item.priority,
        "category": category,
        "area": area if area in AREA_NAMES else None,
        "needs_reply": bool(item.needs_reply),
        "one_line_summary": summary[:300],
    }


def classify_emails(batch: list[dict]) -> list[dict] | None:
    """Classify emails in chunks on the fast model. See AI_CONTRACTS.md 'classify_emails' (stream C).

    Returns the results of every chunk that succeeded; None when nothing succeeded.
    Emails missing from the result fall back to C's rules.
    """
    if not batch:
        return None
    try:
        size = int(get_setting("mail_classify_batch") or DEFAULT_MAIL_BATCH)
    except Exception:
        size = DEFAULT_MAIL_BATCH
    size = max(1, min(size, DEFAULT_MAIL_BATCH))
    out: list[dict] = []
    any_ok = False
    for i in range(0, len(batch), size):
        chunk = batch[i : i + size]
        allowed = {str(e.get("id")) for e in chunk if e.get("id")}
        answer = _call(
            feature="classify_emails",
            switch="mail_classify",
            tier="fast",
            prompt="classify_emails",
            payload={"emails": chunk},
            schema=ClassifyEmailsAnswer,
            max_tokens=160 * len(chunk) + 200,
            cache_system=True,
        )
        if answer is None:
            continue
        any_ok = True
        seen: set[str] = set()
        for item in answer.results:
            cleaned = _clean_email_result(item, allowed)
            if cleaned and cleaned["id"] not in seen:
                seen.add(cleaned["id"])
                out.append(cleaned)
    return out if any_ok else None
