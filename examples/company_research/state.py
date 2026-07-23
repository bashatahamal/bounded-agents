from __future__ import annotations

from typing import Annotated, NotRequired, TypedDict

from bounded.adapters.langgraph import safe_merge


class ResearchState(TypedDict):
    # The only field the graph is actually invoked with -- every other key
    # is populated progressively by nodes, so it's marked NotRequired rather
    # than claiming (falsely) that callers must supply the whole shape.
    company_name: str

    # Raw sources
    website_text: NotRequired[Annotated[str | None, safe_merge]]
    linkedin_text: NotRequired[Annotated[str | None, safe_merge]]

    # Search results (LLM-summarized facets of the raw search snippets)
    search_general: NotRequired[Annotated[str | None, safe_merge]]
    search_founder: NotRequired[Annotated[str | None, safe_merge]]
    search_finance: NotRequired[Annotated[str | None, safe_merge]]
    search_news: NotRequired[Annotated[str | None, safe_merge]]

    # Validation flags
    valid_website: NotRequired[Annotated[bool | None, safe_merge]]
    valid_linkedin: NotRequired[Annotated[bool | None, safe_merge]]
    valid_search: NotRequired[Annotated[bool | None, safe_merge]]
    valid_summary: NotRequired[Annotated[bool | None, safe_merge]]

    # Selected sources (bounded.arbitration.Selection, flattened for state)
    primary_source: NotRequired[Annotated[dict | None, safe_merge]]
    secondary_sources: NotRequired[Annotated[dict | None, safe_merge]]

    # Judge output (bounded.judge.JudgeOutput, flattened for state)
    judge_output: NotRequired[Annotated[dict | None, safe_merge]]

    # Final structured input to the summarizer
    structured_input: NotRequired[Annotated[dict | None, safe_merge]]

    # Step-completion flags
    validated: NotRequired[Annotated[bool | None, safe_merge]]
    sources_selected: NotRequired[Annotated[bool | None, safe_merge]]
    judged: NotRequired[Annotated[bool | None, safe_merge]]
    summarized: NotRequired[Annotated[bool | None, safe_merge]]

    # Final result
    summary: NotRequired[str]

    # Accumulated errors
    errors: NotRequired[Annotated[list[str], safe_merge]]


class SearchResult(TypedDict):
    results: NotRequired[Annotated[str | None, safe_merge]]
