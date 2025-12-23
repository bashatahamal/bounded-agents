from langsmith import traceable

from graphs.states.research import ResearchState
from helpers.json_validators import FIELD_KEYWORDS


@traceable
def validate_sources(state: ResearchState) -> dict:
    """
    Validate sources ONLY when all required inputs are present.
    Otherwise return {} to avoid partial re-triggers.
    """
    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")

    search_keys = [
        "search_general",
        "search_founder",
        "search_finance",
        "search_news",
    ]

    # -----------------------
    # HARD BARRIER: SEARCH NODE COMPLETION
    # -----------------------
    if not all(key in state for key in search_keys):
        return {}

    updates = {"valid_search": True}

    if "website_text" in state:
        updates["valid_website"] = website_text is not None and len(website_text) > 300

    if "linkedin_text" in state:
        updates["valid_linkedin"] = (
            linkedin_text is not None and len(linkedin_text) > 100
        )

    return updates


def missing_fields(primary_text: str) -> list[str]:
    missing = []
    for field, keywords in FIELD_KEYWORDS.items():
        if not any(k.lower() in primary_text.lower() for k in keywords):
            missing.append(field)
    return missing


def select_primary_and_secondary(state: ResearchState) -> dict:
    if state.get("judged", False):
        return {}

    sources = [
        ("website", state.get("website_text"), state.get("valid_website", False)),
        (
            "search",
            {
                "search_general": state.get("search_general"),
                "search_founder": state.get("search_founder"),
                "search_finance": state.get("search_finance"),
                "search_news": state.get("search_news"),
            },
            state.get("valid_search", False),
        ),
        ("linkedin", state.get("linkedin_text"), state.get("valid_linkedin", False)),
        # ("news", state.get("news_text"), state.get("news_valid", False)),
    ]

    def normalize(text):
        if isinstance(text, dict):
            return " ".join(v for v in text.values() if isinstance(v, str))
        return text or ""

    # Keep only valid sources, in priority order
    valid_sources = [
        (name, normalize(text)) for name, text, is_valid in sources if is_valid and text
    ]

    if not valid_sources:
        return {
            "primary_source": {},
            "secondary_sources": {},
            "valid_summary": False,
        }

    primary_name, primary_text = valid_sources[0]
    secondary_sources = {name: text for name, text in valid_sources[1:]}

    missing = missing_fields(primary_text)

    # The judge helps decide which secondary source can safely fill which missing field
    valid_summary = not (len(secondary_sources) > 0 and len(missing) > 0)

    return {
        "primary_source": {
            "source": primary_name,
            "text": primary_text,
        },
        "secondary_sources": secondary_sources,
        "valid_summary": valid_summary,
    }


@traceable
def select_and_validate(state: ResearchState) -> dict:
    # -----------------------------
    # Raw inputs
    # -----------------------------
    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")

    search_text = {
        k: v
        for k, v in {
            "general": state.get("search_general"),
            "founder": state.get("search_founder"),
            "finance": state.get("search_finance"),
            "news": state.get("search_news"),
        }.items()
        if v is not None
    }

    # -----------------------------
    # Validation rules
    # -----------------------------
    valid_website = bool(website_text and len(website_text) > 300)
    valid_linkedin = bool(linkedin_text and len(linkedin_text) > 100)
    valid_search = bool(search_text)

    # -----------------------------
    # Primary source selection
    # Priority: website > linkedin > search
    # -----------------------------
    primary_source = {}
    primary_type = None

    if valid_website:
        primary_source = website_text
        primary_type = "website"
    elif valid_linkedin:
        primary_source = linkedin_text
        primary_type = "linkedin"
    elif valid_search:
        # pick the most general search result first
        primary_source = search_text.get("general") or next(iter(search_text.values()))
        primary_type = "search"

    # -----------------------------
    # Secondary sources
    # -----------------------------
    secondary_sources = {}

    if valid_website and primary_type != "website":
        secondary_sources["website"] = website_text

    if valid_linkedin and primary_type != "linkedin":
        secondary_sources["linkedin"] = linkedin_text

    if valid_search and primary_type != "search":
        secondary_sources["search"] = search_text

    # -----------------------------
    # Single, safe state update
    # -----------------------------
    return {
        "valid_website": valid_website,
        "valid_linkedin": valid_linkedin,
        "valid_search": valid_search,
        "primary_source": {
            "source": primary_type,
            "text": primary_source,
        },
        "secondary_sources": secondary_sources,
    }
