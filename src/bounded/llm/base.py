from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class LLMProvider(Protocol):
    """Minimal surface bounded needs from any LLM backend: one text in, one text out."""

    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str: ...


@dataclass(frozen=True)
class ToolCallRequest:
    """One tool invocation the LLM asked for in a single turn."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ChatResult:
    """One turn of a tool-calling conversation.

    Exactly one of `content` / `tool_calls` is meaningful at a time: a
    turn either answers in text or asks for tools to be run, mirroring how
    OpenAI's tool-calling API itself behaves.
    """

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)


class ToolCallingLLM(Protocol):
    """The surface `bounded.agent.Agent` needs: a chat turn that can request tools.

    Deliberately separate from `LLMProvider` -- not every backend needs to
    support tool calling, and the bounded-judge / summarizer call sites
    should keep depending on the narrower `complete()` surface.
    """

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResult: ...
