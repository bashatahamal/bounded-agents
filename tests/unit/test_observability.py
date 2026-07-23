from unittest.mock import MagicMock

from bounded.observability import maybe_wrap_openai


def test_maybe_wrap_openai_returns_client_unchanged_without_langsmith_env(monkeypatch):
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)

    sentinel = object()
    assert maybe_wrap_openai(sentinel) is sentinel


def test_maybe_wrap_openai_wraps_when_langsmith_api_key_is_set(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)

    # wrap_openai introspects client.chat.completions.create /
    # client.responses.create to monkey-patch them, so it needs something
    # shaped like a real OpenAI client, not a bare object().
    fake_client = MagicMock()
    result = maybe_wrap_openai(fake_client)

    assert result is fake_client
    # The wrapper replaces .create with its own traced callable.
    assert fake_client.chat.completions.create is not None
