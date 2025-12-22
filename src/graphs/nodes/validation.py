from langsmith import traceable

from graphs.states.research import ResearchState


@traceable
def validate_sources(state: ResearchState) -> dict:
    """
    Validate sources ONLY when all required inputs are present.
    Otherwise return {} to avoid partial re-triggers.
    """
    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")

    search_fields = {
        "search_general": state.get("search_general"),
        "search_founder": state.get("search_founder"),
        "search_finance": state.get("search_finance"),
        "search_news": state.get("search_news"),
    }

    # -----------------------
    # HARD GUARD: wait until ALL search_* exist
    # -----------------------
    if not all(search_fields.values()):
        return {}

    # -----------------------
    # HARD GUARD: wait until base texts exist
    # -----------------------
    if website_text is None or linkedin_text is None:
        return {}

    return {
        "valid_website": bool(len(website_text) > 300),
        "valid_linkedin": bool(len(linkedin_text) > 100),
        "valid_search": True,  # all search_* present by guard
    }


def select_primary_and_secondary(state: ResearchState) -> dict:
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

    # Keep only valid sources, in priority order
    valid_sources = [
        (name, text) for name, text, is_valid in sources if is_valid and text
    ]

    if not valid_sources:
        return {
            "primary_source": {},
            "secondary_sources": {},
        }

    primary_name, primary_text = valid_sources[0]

    secondary_sources = {name: text for name, text in valid_sources[1:]}

    return {
        "primary_source": {
            "source": primary_name,
            "text": primary_text,
        },
        "secondary_sources": secondary_sources,
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
