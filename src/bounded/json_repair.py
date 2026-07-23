"""Defensive cleanup for LLM output that's supposed to be JSON but isn't
quite. Shared by `bounded.judge` and `bounded.memory`: both parse schema-
bounded LLM output and must never fabricate a result when it can't be
salvaged, so the cleanup logic is identical.
"""

from __future__ import annotations

import re


def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def normalize_quotes(text: str) -> str:
    return text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")


def remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def clean_json_text(raw: str) -> str:
    """Strip fences, normalize quotes, and drop trailing commas -- the full
    text-cleanup pass. Callers still need `extract_json_object` afterward
    to pull out the `{...}` object itself.
    """
    return remove_trailing_commas(normalize_quotes(strip_markdown_fences(raw.strip())))
