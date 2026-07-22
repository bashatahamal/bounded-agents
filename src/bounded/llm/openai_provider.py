from __future__ import annotations

import json
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from bounded.llm.base import ChatResult, ToolCallRequest
from bounded.observability import maybe_wrap_openai
from bounded.resilience import with_retry


class OpenAIProvider:
    """Thin Chat Completions wrapper implementing `bounded.llm.LLMProvider`
    and `bounded.llm.ToolCallingLLM`.

    Works against any OpenAI-compatible endpoint, not just OpenAI itself --
    pass `base_url` for OpenRouter, Groq, a local vLLM server, etc. `model`
    then needs to be whatever id that endpoint expects (e.g.
    `"openai/gpt-oss-20b:free"` on OpenRouter).
    """

    DEFAULT_MODEL = "gpt-5-mini"
    DEFAULT_TEMPERATURE = 1

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        base_url: str | None = None,
    ) -> None:
        self._client = maybe_wrap_openai(OpenAI(api_key=api_key, base_url=base_url))
        self.model = model
        self.temperature = temperature

    @with_retry(retry_on=(APIConnectionError, APITimeoutError, APIStatusError))
    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str:
        if not user_input and not system_prompt:
            raise ValueError("Either 'user_input' or 'system_prompt' must be provided.")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_input:
            messages.append({"role": "user", "content": user_input})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""

    @with_retry(retry_on=(APIConnectionError, APITimeoutError, APIStatusError))
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResult:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=self.temperature,
        )
        message = response.choices[0].message

        tool_calls = [
            ToolCallRequest(
                id=call.id,
                name=call.function.name,
                arguments=json.loads(call.function.arguments) if call.function.arguments else {},
            )
            for call in (message.tool_calls or [])
        ]

        return ChatResult(content=message.content, tool_calls=tool_calls)
