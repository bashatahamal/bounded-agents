from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Credentials this example needs. Loaded lazily via `get_settings()` --
    never at import time -- so importing the CLI or the agent doesn't
    require a .env to be present.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
