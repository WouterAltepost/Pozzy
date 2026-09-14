from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import select

from app.extensions import db
from app.integrations import claude_client
from app.models import AiCall, Setting


class Answer(BaseModel):
    ok: bool
    message: str


def _call(**overrides):
    kwargs = dict(feature="smoke", switch=None, tier="fast", prompt="ping", payload={"note": "x"}, schema=Answer, max_tokens=64)
    kwargs.update(overrides)
    return claude_client._call(**kwargs)


def _rows():
    return db.session.scalars(select(AiCall).order_by(AiCall.created_at)).all()


def test_happy_path_returns_validated_answer_and_logs(app, fake_claude):
    fake_claude.usage = {"input_tokens": 1000, "output_tokens": 500}
    answer = _call()
    assert answer.ok is True and answer.message == "hi"
    rows = _rows()
    assert len(rows) == 1
    row = rows[0]
    assert row.feature == "smoke" and row.model == app.config["CLAUDE_MODEL_FAST"] and row.ok
    assert row.input_tokens == 1000 and row.output_tokens == 500
    # haiku: 1000 * 1.00 + 500 * 5.00 per million
    assert Decimal(row.cost_estimate) == Decimal("0.003500")
    assert fake_claude.last["model"] == app.config["CLAUDE_MODEL_FAST"]
    assert "Pozzy" not in fake_claude.last_user_text() and '"x"' in fake_claude.last_user_text()


def test_smart_tier_uses_smart_model(app, fake_claude):
    _call(tier="smart")
    assert fake_claude.last["model"] == app.config["CLAUDE_MODEL_SMART"]


def test_malformed_json_returns_none_and_logs_error(app, fake_claude):
    fake_claude.reply = "Sure! Here you go: not json at all"
    assert _call() is None
    row = _rows()[0]
    assert row.ok is False and "JSON" in row.error


def test_json_in_code_fence_and_prose_is_accepted(app, fake_claude):
    fake_claude.reply = 'Here it is:\n```json\n{"ok": false, "message": "fenced"}\n```\nDone.'
    answer = _call()
    assert answer.message == "fenced"


def test_schema_violation_returns_none(app, fake_claude):
    fake_claude.reply = '{"ok": "yes", "msg": 1}'
    assert _call() is None
    assert _rows()[0].ok is False and "ValidationError" in _rows()[0].error


def test_sdk_error_returns_none_and_logs(app, fake_claude):
    fake_claude.error = RuntimeError("boom")
    assert _call() is None
    row = _rows()[0]
    assert row.ok is False and "boom" in row.error and row.input_tokens == 0


def test_truncated_reply_is_a_failure(app, fake_claude):
    fake_claude.stop_reason = "max_tokens"
    assert _call() is None
    assert "max_tokens" in _rows()[0].error


def test_kill_switch_off_skips_call_and_logs_nothing(app, fake_claude):
    row = db.session.scalar(select(Setting).where(Setting.key == "ai_enabled"))
    row.value = {**row.value, "capture": False}
    db.session.commit()
    assert _call(switch="capture") is None
    assert fake_claude.calls == [] and _rows() == []


def test_kill_switch_missing_key_defaults_on(app, fake_claude):
    # seeded ai_enabled has no three_dos key; DEFAULTS say True
    assert _call(switch="three_dos") is not None


def test_no_api_key_returns_none_and_logs(app):
    app.extensions[claude_client.CLIENT_EXTENSION_KEY] = None
    assert _call() is None
    assert "ANTHROPIC_API_KEY" in _rows()[0].error


def test_cache_tokens_priced_and_counted(app, fake_claude):
    fake_claude.usage = {"input_tokens": 100, "output_tokens": 10, "cache_write_tokens": 4000, "cache_read_tokens": 8000}
    _call(cache_system=True)
    row = _rows()[0]
    assert row.input_tokens == 12100
    # 100*1 + 10*5 + 4000*1.25 + 8000*0.10 = 0.000100+0.000050+0.005+0.0008
    assert Decimal(row.cost_estimate) == Decimal("0.005950")
    assert fake_claude.last["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_unknown_model_costs_zero():
    assert claude_client.estimate_cost("claude-future-9", 1000, 1000) == Decimal("0")


def test_price_alias():
    assert claude_client.price_row("claude-haiku-4-5-20251001") == claude_client.PRICES["claude-haiku-4-5"]


def test_ping_wrapper(app, fake_claude):
    assert claude_client.ping("yo") == {"ok": True, "message": "hi"}
    assert "yo" in fake_claude.last_user_text()


def test_load_prompt_sections():
    sections = claude_client.load_prompt("ping")
    assert sections["system"].startswith("You are") and "{{note}}" in sections["user"]
