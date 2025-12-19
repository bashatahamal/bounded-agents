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
        "website_valid": bool(len(website_text) > 300),
        "linkedin_valid": bool(len(linkedin_text) > 100),
        "search_valid": True,  # all search_* present by guard
    }


def select_primary_and_secondary(state: ResearchState) -> dict:
    sources = [
        ("website", state.get("website_text"), state.get("website_valid", False)),
        (
            "search",
            {
                "search_general": state.get("search_general"),
                "search_founder": state.get("search_founder"),
                "search_finance": state.get("search_finance"),
                "search_news": state.get("search_news"),
            },
            state.get("search_valid", False),
        ),
        ("linkedin", state.get("linkedin_text"), state.get("linkedin_valid", False)),
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
    website_valid = bool(website_text and len(website_text) > 300)
    linkedin_valid = bool(linkedin_text and len(linkedin_text) > 100)
    search_valid = bool(search_text)

    # -----------------------------
    # Primary source selection
    # Priority: website > linkedin > search
    # -----------------------------
    primary_source = {}
    primary_type = None

    if website_valid:
        primary_source = website_text
        primary_type = "website"
    elif linkedin_valid:
        primary_source = linkedin_text
        primary_type = "linkedin"
    elif search_valid:
        # pick the most general search result first
        primary_source = search_text.get("general") or next(iter(search_text.values()))
        primary_type = "search"

    # -----------------------------
    # Secondary sources
    # -----------------------------
    secondary_sources = {}

    if website_valid and primary_type != "website":
        secondary_sources["website"] = website_text

    if linkedin_valid and primary_type != "linkedin":
        secondary_sources["linkedin"] = linkedin_text

    if search_valid and primary_type != "search":
        secondary_sources["search"] = search_text

    # -----------------------------
    # Single, safe state update
    # -----------------------------
    return {
        "website_valid": website_valid,
        "linkedin_valid": linkedin_valid,
        "search_valid": search_valid,
        "primary_source": {
            "source": primary_type,
            "text": primary_source,
        },
        "secondary_sources": secondary_sources,
    }
