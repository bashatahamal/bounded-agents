from __future__ import annotations

from bounded.arbitration import Source, select
from company_research.fields import FIELD_KEYWORDS
from company_research.state import ResearchState

SEARCH_KEYS = ["search_general", "search_founder", "search_finance", "search_news"]


def validate_sources(state: ResearchState) -> dict:
    """Validate sources ONLY once all required inputs are present.

    LangGraph re-invokes this node as each parallel fetch branch (website,
    LinkedIn, the four search facets) completes; returning {} until every
    branch has reported in avoids doing real work on partial state.
    """
    if not all(key in state for key in SEARCH_KEYS):
        return {}

    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")

    updates: dict = {"valid_search": True}
    if "website_text" in state:
        updates["valid_website"] = website_text is not None and len(website_text) > 300
    if "linkedin_text" in state:
        updates["valid_linkedin"] = linkedin_text is not None and len(linkedin_text) > 100

    return updates


def _normalize(text: str | dict | None) -> str:
    if isinstance(text, dict):
        return " ".join(v for v in text.values() if isinstance(v, str))
    return text or ""


def select_primary_and_secondary(state: ResearchState) -> dict:
    if state.get("judged", False):
        return {}

    search_blob = {
        "search_general": state.get("search_general"),
        "search_founder": state.get("search_founder"),
        "search_finance": state.get("search_finance"),
        "search_news": state.get("search_news"),
    }

    # Priority order IS the authority rule: website > search > LinkedIn.
    # Deciding this in code (not via a prompt) is the load-bearing idea in
    # docs/DESIGN.md -- see bounded.arbitration for the mechanism.
    website_text = _normalize(state.get("website_text"))
    linkedin_text = _normalize(state.get("linkedin_text"))
    search_text = _normalize(search_blob)

    sources = [
        Source("website", website_text, bool(state.get("valid_website"))),
        Source("search", search_text, bool(state.get("valid_search"))),
        Source("linkedin", linkedin_text, bool(state.get("valid_linkedin"))),
    ]

    selection = select(sources, FIELD_KEYWORDS)

    if selection.primary is None:
        return {"primary_source": {}, "secondary_sources": {}, "valid_summary": False}

    return {
        "primary_source": {"source": selection.primary.name, "text": selection.primary.text},
        "secondary_sources": {s.name: s.text for s in selection.secondary},
        "valid_summary": selection.complete,
    }
