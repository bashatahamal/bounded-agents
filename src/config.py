import json
from typing import Any

import structlog
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from helpers.read_markdown import read_markdown_file_to_dict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    TAVILY_API_KEY: str = Field(..., description="Tavily API key for web search")
    SERPER_API_KEY: str = Field(..., description="Serper API key for web search")
    GOOGLE_SHEET_ACCESS_CREDS: str = Field(..., description="Google Sheets access key JSON string")
    GOOGLE_SHEET_ACCESS_DICT: dict[str, Any] = Field(default_factory=dict, description="Parsed Google Sheets access key")

    def _parse_json_recursive(data: str, max_attempts: int = 3) -> dict[str, Any]:
        """Recursively parse JSON string, handling nested JSON."""
        current_data = data

        for attempt in range(max_attempts):
            try:
                parsed = json.loads(current_data)

                # If result is dict, we're done
                if isinstance(parsed, dict):
                    logger.debug(f"Successfully parsed JSON on attempt {attempt + 1}")
                    return parsed

                # If result is still string, try parsing again
                elif isinstance(parsed, str):
                    current_data = parsed
                    logger.debug(
                        f"Attempt {attempt + 1}: Got nested JSON string, trying again"
                    )
                    continue

                else:
                    raise ValueError(
                        f"Unexpected type after JSON parsing: {type(parsed)}"
                    )

            except json.JSONDecodeError as e:
                if attempt == 0:
                    # Try to clean up common issues on first attempt
                    cleaned = current_data.strip().strip("\"'")
                    if cleaned != current_data:
                        current_data = cleaned
                        logger.debug("Cleaned up quotes, retrying...")
                        continue

                logger.error(f"JSON parsing failed on attempt {attempt + 1}: {e}")
                raise ValueError(f"Invalid JSON in GOOGLE_SHEET_ACCESS_CREDS: {e}")

        raise ValueError("Max parsing attempts reached")

    @field_validator("GOOGLE_SHEET_ACCESS_DICT", mode="before")
    @classmethod
    def parse_google_sheet_access_key(cls, v: Any, info) -> dict[str, Any]:
        """Parse the GOOGLE_SHEET_ACCESS_CREDS JSON string into a dictionary."""

        if v and not isinstance(v, dict):
            return v

        if hasattr(info, "data") and "GOOGLE_SHEET_ACCESS_CREDS" in info.data:
            access_key = info.data["GOOGLE_SHEET_ACCESS_CREDS"]
            try:
                gs_access = cls._parse_json_recursive(access_key)
                if gs_access == {}:
                    raise ValueError("Failed parsed google spreadheet creds!")
                logger.debug("Successfully Parsed Google Sheets Creds!")
                return gs_access
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEET_ACCESS_DICT: {e}")

        raise ValueError("Invalid Google Access Creds!")


logger.info("Loading settings...")
settings = Settings()
prompt_general = read_markdown_file_to_dict("src/prompts/general.md")
logger.info("Loaded settings!")
