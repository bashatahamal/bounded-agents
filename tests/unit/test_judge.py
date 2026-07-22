import pytest

from bounded.judge import JudgeError, JudgeOutput, parse_judge_output, run_bounded_judge

ALLOWED = {"industry", "founders"}


def test_parse_judge_output_happy_path():
    raw = """
    {
        "missing_fields": ["founders"],
        "field_enrichment": {
            "founders": {"use_secondary": true, "source": "linkedin", "reason": "..."}
        },
        "bias_flags": {"linkedin": "marketing language"}
    }
    """
    result = parse_judge_output(raw, ALLOWED)

    assert result.missing_fields == ["founders"]
    assert result.field_enrichment == {
        "founders": {"use_secondary": True, "source": "linkedin", "reason": "..."}
    }
    assert result.bias_flags == {"linkedin": "marketing language"}


def test_parse_judge_output_strips_markdown_fences():
    raw = '```json\n{"missing_fields": [], "field_enrichment": {}, "bias_flags": {}}\n```'
    result = parse_judge_output(raw, ALLOWED)
    assert result == JudgeOutput(missing_fields=[], field_enrichment={}, bias_flags={})


def test_parse_judge_output_normalizes_smart_quotes_and_trailing_commas():
    raw = '{“missing_fields”: [],  "field_enrichment": {},"bias_flags": {},}'
    result = parse_judge_output(raw, ALLOWED)
    assert result.missing_fields == []


def test_parse_judge_output_drops_fields_outside_allowed_set():
    raw = (
        '{"missing_fields": [], '
        '"field_enrichment": {"founders": {"use_secondary": true, "source": "x"}, '
        '"totally_invented_field": {"use_secondary": true, "source": "x"}}, '
        '"bias_flags": {}}'
    )
    result = parse_judge_output(raw, ALLOWED)
    assert set(result.field_enrichment.keys()) == {"founders"}


def test_parse_judge_output_raises_on_no_json_object():
    with pytest.raises(JudgeError):
        parse_judge_output("no json here at all", ALLOWED)


def test_parse_judge_output_raises_on_malformed_json():
    with pytest.raises(JudgeError):
        parse_judge_output("{not: valid, json", ALLOWED)


def test_parse_judge_output_raises_when_top_level_is_not_an_object():
    with pytest.raises(JudgeError):
        parse_judge_output("[1, 2, 3]", ALLOWED)


class _StubLLM:
    def __init__(self, response: str):
        self._response = response

    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str:
        return self._response


def test_run_bounded_judge_calls_llm_and_parses_result():
    llm = _StubLLM('{"missing_fields": ["founders"], "field_enrichment": {}, "bias_flags": {}}')

    result = run_bounded_judge(llm=llm, prompt="irrelevant", allowed_fields=ALLOWED)

    assert result.missing_fields == ["founders"]


def test_run_bounded_judge_propagates_judge_error_on_bad_output():
    llm = _StubLLM("not json")

    with pytest.raises(JudgeError):
        run_bounded_judge(llm=llm, prompt="irrelevant", allowed_fields=ALLOWED)
