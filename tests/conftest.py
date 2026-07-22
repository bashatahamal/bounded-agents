import pytest


@pytest.fixture(autouse=True)
def _fake_credentials(monkeypatch):
    """Every test gets fake-but-present credentials, and every lru_cache'd
    singleton that might have been built by an earlier test is cleared
    first -- settings and clients are process-wide caches, so leaking one
    test's patched state into the next would produce flaky, order-dependent
    failures.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("SERPER_API_KEY", "test-serper-key")
    monkeypatch.setenv("GOOGLE_SHEET_ACCESS_CREDS", '{"type": "service_account"}')

    from company_research import fetchers, llm_client, settings

    settings.get_settings.cache_clear()
    llm_client.get_llm_client.cache_clear()
    fetchers._tavily_client.cache_clear()

    yield

    settings.get_settings.cache_clear()
    llm_client.get_llm_client.cache_clear()
    fetchers._tavily_client.cache_clear()
