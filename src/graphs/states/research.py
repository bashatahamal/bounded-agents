# from typing import Dict, Optional, TypedDict
# from typing_extensions import Annotated
# from langgraph.channels import Topic
# import operator


# class ResearchState(TypedDict):
#     company_name: str

#     # Raw sources
#     website_text: Annotated[str, operator.add]
#     linkedin_text: Annotated[str, operator.add]
#     search_text: Annotated[str, operator.add]

#     # search results
#     search_general: Annotated[str, operator.add]
#     search_founder: Annotated[str, operator.add]
#     search_finance: Annotated[str, operator.add]
#     search_news: Annotated[str, operator.add]

#     # Validation
#     website_valid: Annotated[bool, operator.add]
#     linkedin_valid: Annotated[bool, operator.add]
#     search_valid: Annotated[bool, operator.add]

#     # Selected / merged inputs
#     primary_source:  Annotated[dict, operator.add]
#     secondary_sources:  Annotated[dict, operator.add]

#     # Judge output (optional, may be None)
#     judge_output:  Annotated[dict, operator.add]

#     # Final structured input to summarizer
#     structured_input: Annotated[dict, operator.add]

#     # Final result
#     summary: Optional[str]

#     errors: Annotated[list[str], operator.add]

# class SearchResult(TypedDict):
#     results: Annotated[str, operator.add]


from typing import Any, Dict, List, Optional, TypedDict

from typing_extensions import Annotated


def safe_merge(a: Any, b: Any) -> Any:
    """
    Universal LangGraph merge function.
    - None-safe
    - Type-aware
    - Deterministic
    """

    # -------------------------
    # Handle None
    # -------------------------
    if a is None:
        return b
    if b is None:
        return a

    # -------------------------
    # Lists → concatenate
    # -------------------------
    if isinstance(a, list) and isinstance(b, list):
        return a + b

    # -------------------------
    # Dicts → shallow merge (b wins)
    # -------------------------
    if isinstance(a, dict) and isinstance(b, dict):
        merged = dict(a)
        merged.update(b)
        return merged

    # -------------------------
    # Booleans → last write wins
    # -------------------------
    if isinstance(a, bool) and isinstance(b, bool):
        return b

    # -------------------------
    # Strings → last write wins
    # (concatenation is usually wrong semantically)
    # -------------------------
    if isinstance(a, str) and isinstance(b, str):
        return b

    # -------------------------
    # Fallback → last write wins
    # -------------------------
    return b


class ResearchState(TypedDict):
    company_name: str

    # Raw sources
    website_text: Annotated[Optional[str], safe_merge]
    linkedin_text: Annotated[Optional[str], safe_merge]
    search_text: Annotated[Optional[str], safe_merge]

    # Search results
    search_general: Annotated[Optional[str], safe_merge]
    search_founder: Annotated[Optional[str], safe_merge]
    search_finance: Annotated[Optional[str], safe_merge]
    search_news: Annotated[Optional[str], safe_merge]

    # Validation flags
    website_valid: Annotated[Optional[bool], safe_merge]
    linkedin_valid: Annotated[Optional[bool], safe_merge]
    search_valid: Annotated[Optional[bool], safe_merge]

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
