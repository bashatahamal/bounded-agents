from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol


class JudgeError(Exception):
    """Raised when a bounded judge's LLM output can't be salvaged into valid JSON."""


@dataclass(frozen=True)
class JudgeOutput:
    missing_fields: list[str]
    field_enrichment: dict[str, dict]
    bias_flags: dict[str, str]


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _normalize_quotes(text: str) -> str:
    return text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def parse_judge_output(raw: str, allowed_fields: set[str]) -> JudgeOutput:
    """Defensively parse an LLM judge's raw text into a JudgeOutput.

    LLMs wrap JSON in code fences, use smart quotes, and leave trailing
    commas -- this cleans those up, extracts the JSON object, and drops any
    field name the judge invented that isn't in `allowed_fields`. The judge
    can flag gaps and recommend which approved secondary source fills which
    field; it cannot expand the schema or introduce a field on its own.

    Raises `JudgeError` (never returns a fabricated result) if the output
    can't be salvaged -- callers should treat that the same as "judge
    unavailable" and fall back to the deterministic selection.
    """
    text = _remove_trailing_commas(_normalize_quotes(_strip_markdown_fences(raw.strip())))

    json_text = _extract_json_object(text)
    if not json_text:
        raise JudgeError(f"No JSON object found in judge output: {raw!r}")

    try:
        parsed = json.loads(json_text, strict=False)
    except json.JSONDecodeError as exc:
        raise JudgeError(f"Judge output is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise JudgeError(f"Judge output must be a JSON object, got {type(parsed).__name__}")

    field_enrichment = parsed.get("field_enrichment", {})
    if isinstance(field_enrichment, dict):
        field_enrichment = {
            key.strip().strip('"'): value
            for key, value in field_enrichment.items()
            if key.strip().strip('"') in allowed_fields and isinstance(value, dict)
        }
    else:
        field_enrichment = {}

    bias_flags = parsed.get("bias_flags", {})

    return JudgeOutput(
        missing_fields=list(parsed.get("missing_fields", [])),
        field_enrichment=field_enrichment,
        bias_flags=dict(bias_flags) if isinstance(bias_flags, dict) else {},
    )


class JudgeLLM(Protocol):
    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str: ...


def run_bounded_judge(*, llm: JudgeLLM, prompt: str, allowed_fields: set[str]) -> JudgeOutput:
    """Call an LLM with a prepared prompt and parse its output as a bounded judge.

    The judge is explicitly bounded: it can only report gaps and recommend
    which already-approved secondary source should fill which field. It
    cannot introduce new sources or invent facts -- `bounded.arbitration`
    already decided which sources are eligible before this is ever called,
    and `parse_judge_output` enforces the schema on the way back out.
    """
    raw = llm.complete(user_input=prompt)
    return parse_judge_output(raw, allowed_fields)
