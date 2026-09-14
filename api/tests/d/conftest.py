"""Stream D fixtures: a fake Anthropic client injected into the app, no network."""
from types import SimpleNamespace

import pytest

from app.integrations import claude_client
from conftest import bearer


class FakeMessages:
    def __init__(self, owner):
        self.owner = owner

    def create(self, **kwargs):
        self.owner.calls.append(kwargs)
        if self.owner.error is not None:
            raise self.owner.error
        replies = self.owner.replies
        text = replies.pop(0) if replies else self.owner.reply
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            stop_reason=self.owner.stop_reason,
            usage=SimpleNamespace(
                input_tokens=self.owner.usage.get("input_tokens", 100),
                output_tokens=self.owner.usage.get("output_tokens", 20),
                cache_creation_input_tokens=self.owner.usage.get("cache_write_tokens", 0),
                cache_read_input_tokens=self.owner.usage.get("cache_read_tokens", 0),
            ),
        )


class FakeAnthropic:
    """Stands in for anthropic.Anthropic. Set `reply` (or a `replies` queue), `error`, `stop_reason`, `usage`."""

    def __init__(self, reply='{"ok": true, "message": "hi"}'):
        self.reply = reply
        self.replies: list[str] = []
        self.error: Exception | None = None
        self.stop_reason = "end_turn"
        self.usage: dict = {}
        self.calls: list[dict] = []
        self.messages = FakeMessages(self)

    @property
    def last(self) -> dict:
        return self.calls[-1]

    def last_user_text(self) -> str:
        return self.last["messages"][0]["content"]


@pytest.fixture
def fake_claude(app):
    fake = FakeAnthropic()
    app.extensions[claude_client.CLIENT_EXTENSION_KEY] = fake
    return fake


@pytest.fixture
def headers(token_factory):
    return bearer(token_factory())
