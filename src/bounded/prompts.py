from __future__ import annotations

import re
from pathlib import Path


def load_markdown_sections(path: str | Path) -> dict[str, str]:
    """Split a Markdown file into `{heading: content}` by top-level `## ` headings.

    Keeps prompt text in editable .md files instead of Python string
    literals: each `## heading` becomes a dict key, its body (up to the next
    `## `) becomes the value.
    """
    text = Path(path).read_text(encoding="utf-8")
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]

    result: dict[str, str] = {}
    for section in sections:
        heading, *rest = section.split("\n")
        result[heading.strip()] = "\n".join(rest).strip()
    return result
