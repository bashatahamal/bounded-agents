from bounded.llm.openai_provider import OpenAIProvider


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
