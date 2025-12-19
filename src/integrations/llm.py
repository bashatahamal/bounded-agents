from typing import Literal, Optional

from langsmith.wrappers import wrap_openai
from openai import OpenAI

from config import settings
import asyncio

class LLMClient:
    """Thin wrapper around the OpenAI Chat Completions API."""

    DEFAULT_MODEL = "gpt-5-mini"
    DEFAULT_TEMPERATURE = 1

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = wrap_openai(OpenAI(api_key=api_key or settings.OPENAI_API_KEY))

    def completion(
        self,
        *,
        user_input: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """
        Generate a single completion.

        Usage patterns:
        - user only
        - system only
        - system + user

        :param user_input: User message content.
        :param system_prompt: System instruction.
        :param model: Model name.
        :param temperature: Sampling temperature.
        :return: Generated text.
        """
        if not user_input and not system_prompt:
            raise ValueError("Either 'user' or 'system' must be provided.")

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if user_input:
            messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""

    def completion_with_websearch(
        self,
        user_input: str,
        *,
        model: Literal[
            "gpt-4o-mini-search-preview",
            "gpt-4o-search-preview",
        ] = "gpt-4o-mini-search-preview",
    ) -> str:
        """
        Generate a response using OpenAI's web search–enabled models.

        :param user_input: User query.
        :param model: Search-enabled model.
        :return: Generated text response.
        """
        response = self.client.chat.completions.create(
            model=model,
            web_search_options={},
            messages=[
                {"role": "user", "content": user_input},
            ],
        )

        return response.choices[0].message.content or ""
    
    
    async def completion_async(
        self,
        *,
        user_input: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.completion(
                user_input=user_input,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
            ),
        )

    @staticmethod
    def _build_messages(
        user_input: str,
        system_prompt: Optional[str] = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_input})

        return messages


# Eager load singleton
llm_client = LLMClient()


if __name__ == "__main__":
    result = llm_client.generate("Hello")
    print(result)
