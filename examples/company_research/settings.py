from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Credentials this example needs. Loaded lazily via `get_settings()` --
    never at import time -- so `--help` and unit tests work without a .env.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    TAVILY_API_KEY: str = Field(..., description="Tavily search API key")
    SERPER_API_KEY: str = Field(..., description="Serper (Google Search API) key")
    GOOGLE_SHEET_ACCESS_CREDS: str = Field(
        ..., description="Google service account credentials: file path, base64, or raw JSON"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read and validate settings from the environment, once per process.

    Deliberately not called at module import time anywhere in this example
    -- only from inside functions that are actually about to make a network
    call -- so importing the CLI or the graph never requires credentials to
    be present.
    """
    return Settings()
