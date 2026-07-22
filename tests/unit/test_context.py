from bounded.context import ContextSource, build_context_pack


def test_build_context_pack_orders_by_priority_not_input_order():
    sources = [
        ContextSource("low", "low priority content", priority=3),
        ContextSource("high", "high priority content", priority=1),
        ContextSource("mid", "mid priority content", priority=2),
    ]

    pack = build_context_pack(sources)

    assert pack.index("high") < pack.index("mid") < pack.index("low")


def test_build_context_pack_includes_everything_without_a_budget():
    sources = [ContextSource("a", "x" * 50, priority=1), ContextSource("b", "y" * 50, priority=2)]

    pack = build_context_pack(sources)

    assert "a" in pack and "b" in pack


def test_build_context_pack_drops_whole_lowest_priority_sources_over_budget():
    sources = [
        ContextSource("rules", "R" * 100, priority=1),
        ContextSource("memory", "M" * 100, priority=2),
        ContextSource("activity", "A" * 100, priority=3),
    ]

    pack = build_context_pack(sources, max_chars=110)

    assert "## rules" in pack
    assert "## memory" not in pack
    assert "## activity" not in pack


def test_build_context_pack_never_truncates_mid_source():
    sources = [ContextSource("rules", "R" * 100, priority=1)]

    pack = build_context_pack(sources, max_chars=50)

    # The one source doesn't fit at all -> dropped whole, not cut short.
    assert "rules" not in pack
    assert pack == ""


def test_build_context_pack_stops_at_first_source_that_does_not_fit():
    # A later, smaller source should NOT be pulled in ahead of a bigger one
    # that was skipped -- priority order is a strict prefix, not bin-packing.
    sources = [
        ContextSource("first", "F" * 80, priority=1),
        ContextSource("second_too_big", "S" * 80, priority=2),
        ContextSource("third_would_fit_alone", "T" * 5, priority=3),
    ]

    pack = build_context_pack(sources, max_chars=90)

    assert "## first" in pack
    assert "second_too_big" not in pack
    assert "third_would_fit_alone" not in pack
