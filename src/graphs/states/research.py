from typing import Dict, Optional, TypedDict
from typing_extensions import Annotated
from langgraph.channels import Topic
import operator


class ResearchState(TypedDict):
    company_name: str

    # Raw sources
    website_text: Optional[str]
    linkedin_text: Optional[str]
    search_text: Optional[Dict]

    # search results
    search_general: Optional[str]
    search_founder: Optional[str]
    search_finance: Optional[str]
    search_news: Optional[str]

    # Validation
    website_valid: bool
    linkedin_valid: bool
    search_valid: bool

    # Selected / merged inputs
    primary_source: Dict[str, str]
    secondary_sources: Dict[str, str]

    # Judge output (optional, may be None)
    judge_output: Optional[Dict]

    # Final structured input to summarizer
    structured_input: Dict[str, str]

    # Final result
    summary: Optional[str]

    errors: Annotated[list[str], operator.add]

class SearchResult(TypedDict):
    results: Optional[str]
