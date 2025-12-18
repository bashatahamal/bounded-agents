from graphs.states.research import ResearchState
from langsmith import traceable

@traceable
def validate_sources(state: ResearchState) -> dict:
    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")
    search_text = state.get("search_text")

    return {
        "website_valid": bool(website_text and len(website_text) > 300),
        "linkedin_valid": bool(linkedin_text and len(linkedin_text) > 100),
        "search_valid": bool(search_text and len(search_text) > 50),
    }


def select_primary_and_secondary(state: ResearchState) -> dict:
    sources = [
        ("website", state.get("website_text"), state.get("website_valid", False)),
        ("linkedin", state.get("linkedin_text"), state.get("linkedin_valid", False)),
        ("search", state.get("search_text"), state.get("search_valid", False)),
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
