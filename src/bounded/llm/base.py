from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    """Minimal surface bounded needs from any LLM backend: one text in, one text out."""

    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str: ...
