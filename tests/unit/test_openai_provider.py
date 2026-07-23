import pytest

from bounded.llm.openai_provider import EmptyCompletionError, OpenAIProvider


def test_default_base_url_targets_openai():
    provider = OpenAIProvider(api_key="sk-fake")

    assert str(provider._client.base_url) == "https://api.openai.com/v1/"


def test_custom_base_url_is_passed_through_for_openai_compatible_endpoints():
    provider = OpenAIProvider(
        api_key="sk-or-fake",
        model="openai/gpt-oss-20b:free",
        base_url="https://openrouter.ai/api/v1",
    )

    assert str(provider._client.base_url) == "https://openrouter.ai/api/v1/"
    assert provider.model == "openai/gpt-oss-20b:free"


class _EmptyChoicesResponse:
    """Mimics an OpenAI ChatCompletion whose `choices` came back empty --
    seen in practice against a free OpenRouter model returning a
    degraded-but-200 response."""

    choices: list = []

    def model_dump_json(self) -> str:
        return '{"choices": [], "note": "fake empty response for a test"}'


def test_chat_raises_a_clear_error_when_response_has_no_choices(monkeypatch):
    provider = OpenAIProvider(api_key="sk-fake", model="test-model")
    monkeypatch.setattr(
        provider._client.chat.completions, "create", lambda **kw: _EmptyChoicesResponse()
    )

    with pytest.raises(EmptyCompletionError, match="test-model"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], tools=[])


def test_complete_raises_a_clear_error_when_response_has_no_choices(monkeypatch):
    provider = OpenAIProvider(api_key="sk-fake", model="test-model")
    monkeypatch.setattr(
        provider._client.chat.completions, "create", lambda **kw: _EmptyChoicesResponse()
    )

    with pytest.raises(EmptyCompletionError, match="test-model"):
        provider.complete(user_input="hi")


def test_chat_retries_and_recovers_from_one_empty_response(monkeypatch):
    """Confirms EmptyCompletionError is wired into with_retry's retry_on --
    a transient empty response shouldn't fail the whole turn if a retry
    would have succeeded."""
    provider = OpenAIProvider(api_key="sk-fake", model="test-model")
    calls = {"n": 0}

    fake_message = type("Msg", (), {"content": "ok", "tool_calls": None})()
    fake_choice = type("Choice", (), {"message": fake_message})()

    class _RealResponse:
        choices = [fake_choice]

    def flaky_create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _EmptyChoicesResponse()
        return _RealResponse()

    monkeypatch.setattr(provider._client.chat.completions, "create", flaky_create)

    result = provider.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

    assert result.content == "ok"
    assert calls["n"] == 2
