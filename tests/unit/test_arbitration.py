from bounded.arbitration import Source, missing_fields, select

FIELD_KEYWORDS = {
    "industry": ["industry", "sector"],
    "founders": ["founder", "co-founder"],
}


def test_missing_fields_flags_uncovered_keywords():
    text = "Acme operates in the fintech industry."
    assert missing_fields(text, FIELD_KEYWORDS) == ["founders"]


def test_missing_fields_none_when_all_covered():
    text = "Acme is in the fintech industry. Its founder is Jane Doe."
    assert missing_fields(text, FIELD_KEYWORDS) == []


def test_select_picks_first_valid_source_as_primary_in_priority_order():
    website = Source("website", "Acme is in the fintech industry, founded by Jane.", True)
    linkedin = Source("linkedin", "some linkedin text", True)

    selection = select([website, linkedin], FIELD_KEYWORDS)

    assert selection.primary is website
    assert selection.secondary == (linkedin,)


def test_select_skips_invalid_sources_regardless_of_position():
    website = Source("website", "too short", False)
    search = Source("search", "Acme is in the fintech industry, founded by Jane.", True)
    linkedin = Source("linkedin", None, False)

    selection = select([website, search, linkedin], FIELD_KEYWORDS)

    assert selection.primary is search
    assert selection.secondary == ()


def test_select_returns_no_primary_when_nothing_valid():
    sources = [Source("website", None, False), Source("linkedin", None, False)]

    selection = select(sources, FIELD_KEYWORDS)

    assert selection.primary is None
    assert selection.secondary == ()
    assert selection.complete is False


def test_select_incomplete_only_when_secondary_could_fill_a_gap():
    # Primary is missing "founders" and there IS a secondary source -> incomplete,
    # a bounded judge should be considered.
    primary = Source("website", "Acme is in the fintech industry.", True)
    secondary = Source("linkedin", "Acme was founded by Jane Doe.", True)

    selection = select([primary, secondary], FIELD_KEYWORDS)

    assert selection.missing_fields == ("founders",)
    assert selection.complete is False


def test_select_complete_when_nothing_to_enrich_with_even_if_fields_missing():
    # Primary is missing "founders" but there's no secondary source at all ->
    # nothing a judge could do, so it's still considered complete (skip the judge).
    primary = Source("website", "Acme is in the fintech industry.", True)

    selection = select([primary], FIELD_KEYWORDS)

    assert selection.missing_fields == ("founders",)
    assert selection.complete is True


def test_select_complete_when_primary_covers_everything_despite_secondaries():
    primary = Source("website", "Acme is in the fintech industry. Its founder is Jane.", True)
    secondary = Source("linkedin", "some linkedin text", True)

    selection = select([primary, secondary], FIELD_KEYWORDS)

    assert selection.missing_fields == ()
    assert selection.complete is True
