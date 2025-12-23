from typing import Optional, TypedDict

from typing_extensions import Annotated

from helpers.state_addition import safe_merge


class ResearchState(TypedDict):
    company_name: str

    # Raw sources
    website_text: Annotated[Optional[str], safe_merge]
    linkedin_text: Annotated[Optional[str], safe_merge]
    # search_text: Annotated[Optional[str], safe_merge]

    # Search results
    search_general: Annotated[Optional[str], safe_merge]
    search_founder: Annotated[Optional[str], safe_merge]
    search_finance: Annotated[Optional[str], safe_merge]
    search_news: Annotated[Optional[str], safe_merge]

    # Validation flags
    valid_website: Annotated[Optional[bool], safe_merge]
    valid_linkedin: Annotated[Optional[bool], safe_merge]
    valid_search: Annotated[Optional[bool], safe_merge]
    valid_summary: Annotated[Optional[bool], safe_merge]

    # Selected sources
    primary_source: Annotated[Optional[dict], safe_merge]
    secondary_sources: Annotated[Optional[dict], safe_merge]

    # Judge output
    judge_output: Annotated[Optional[dict], safe_merge]

    # Final structured input
    structured_input: Annotated[Optional[dict], safe_merge]

    # Validation flags
    validated: Annotated[Optional[bool], safe_merge]
    sources_selected: Annotated[Optional[bool], safe_merge]
    judged: Annotated[Optional[bool], safe_merge]
    summarized: Annotated[Optional[bool], safe_merge]

    # Final result
    summary: str

    # Accumulated errors
    errors: Annotated[list[str], safe_merge]
    aggregated_inputs: dict | None


class SearchResult(TypedDict):
    results: Annotated[Optional[str], safe_merge]
