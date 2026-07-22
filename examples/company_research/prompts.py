from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from bounded.prompts import load_markdown_sections

PROMPTS_PATH = Path(__file__).parent / "prompts" / "general.md"


@lru_cache(maxsize=1)
def get_prompts() -> dict[str, str]:
    return load_markdown_sections(PROMPTS_PATH)
