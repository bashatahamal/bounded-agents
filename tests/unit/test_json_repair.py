from bounded.json_repair import (
    clean_json_text,
    extract_json_object,
    normalize_quotes,
    remove_trailing_commas,
    strip_markdown_fences,
)


def test_strip_markdown_fences_removes_json_code_fence():
    assert strip_markdown_fences('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_markdown_fences_leaves_unfenced_text_alone():
    assert strip_markdown_fences('{"a": 1}') == '{"a": 1}'


def test_normalize_quotes_converts_smart_quotes_to_straight():
    assert normalize_quotes("“hello” ‘world’") == "\"hello\" 'world'"


def test_remove_trailing_commas_before_closing_brackets():
    assert remove_trailing_commas('{"a": 1,}') == '{"a": 1}'
    assert remove_trailing_commas("[1, 2,]") == "[1, 2]"


def test_extract_json_object_pulls_out_the_braces():
    assert extract_json_object('noise before {"a": 1} noise after') == '{"a": 1}'


def test_extract_json_object_returns_none_without_braces():
    assert extract_json_object("no json here") is None


def test_clean_json_text_runs_the_full_pipeline():
    raw = "```json\n{“a”: 1,}\n```"
    assert clean_json_text(raw) == '{"a": 1}'
