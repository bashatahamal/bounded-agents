from __future__ import annotations

from functools import lru_cache

from bounded.llm.openai_provider import OpenAIProvider
from company_research.settings import get_settings


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAIProvider:
    """Lazily built, cached OpenAI provider -- reads settings on first call, not at import."""
    return OpenAIProvider(api_key=get_settings().OPENAI_API_KEY)
