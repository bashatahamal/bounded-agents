from bounded.prompts import load_markdown_sections


def test_load_markdown_sections_splits_on_h2_headings(tmp_path):
    path = tmp_path / "prompts.md"
    path.write_text(
        "## first\nline one\nline two\n\n## second\ncontent here\n",
        encoding="utf-8",
    )

    sections = load_markdown_sections(path)

    assert sections == {
        "first": "line one\nline two",
        "second": "content here",
    }


def test_load_markdown_sections_ignores_text_before_first_heading(tmp_path):
    path = tmp_path / "prompts.md"
    path.write_text("preamble, not a section\n\n## real\nbody\n", encoding="utf-8")

    sections = load_markdown_sections(path)

    assert sections == {"real": "body"}
