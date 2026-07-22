from company_research.nodes.validate import (
    SEARCH_KEYS,
    select_primary_and_secondary,
    validate_sources,
)


def _full_search_state(**overrides):
    state = {
        "search_general": "general",
        "search_founder": "founder",
        "search_finance": "finance",
        "search_news": "news",
        "website_text": "x" * 400,
        "linkedin_text": "y" * 150,
    }
    state.update(overrides)
    return state


def test_validate_sources_returns_empty_until_all_search_keys_present():
    partial_state = {"website_text": "x" * 400}
    assert validate_sources(partial_state) == {}


def test_validate_sources_flags_short_website_and_linkedin_as_invalid():
    state = _full_search_state(website_text="too short", linkedin_text="also short")
    result = validate_sources(state)
    assert result["valid_website"] is False
    assert result["valid_linkedin"] is False
    assert result["valid_search"] is True


def test_validate_sources_flags_long_enough_sources_as_valid():
    state = _full_search_state()
    result = validate_sources(state)
    assert result["valid_website"] is True
    assert result["valid_linkedin"] is True


def test_search_keys_constant_matches_the_four_facets():
    assert SEARCH_KEYS == ["search_general", "search_founder", "search_finance", "search_news"]


def test_select_primary_and_secondary_prefers_website_over_search_and_linkedin():
    # This text only covers a couple of the ten domain fields (industry,
    # founders) -- it deliberately does NOT cover all of them, so the
    # selection should come back incomplete and defer to the judge, which
    # is the realistic case this arbitration step exists to detect.
    state = {
        "website_text": (
            "Acme is a fintech company in the payments industry, founded by Jane Doe, "
            "offering a platform for enterprise customers with a subscription business model."
        ),
        "valid_website": True,
        "valid_linkedin": True,
        "linkedin_text": "Acme on LinkedIn",
        "valid_search": True,
        "search_general": "general info",
        "search_founder": "founder info",
        "search_finance": "finance info",
        "search_news": "news info",
    }

    result = select_primary_and_secondary(state)

    assert result["primary_source"]["source"] == "website"
    assert set(result["secondary_sources"].keys()) == {"search", "linkedin"}
    assert result["valid_summary"] is False


def test_select_primary_and_secondary_falls_back_when_nothing_valid():
    state = {"valid_website": False, "valid_linkedin": False, "valid_search": False}

    result = select_primary_and_secondary(state)

    assert result == {"primary_source": {}, "secondary_sources": {}, "valid_summary": False}


def test_select_primary_and_secondary_short_circuits_once_judged():
    state = {"judged": True}
    assert select_primary_and_secondary(state) == {}
