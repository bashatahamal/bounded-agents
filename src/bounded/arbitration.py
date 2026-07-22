from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """One candidate piece of evidence, in caller-defined priority order."""

    name: str
    text: str | None
    valid: bool


@dataclass(frozen=True)
class Selection:
    """The deterministic result of arbitrating between sources.

    `complete` is False only when there ARE secondary sources that could
    plausibly fill a gap the primary source has -- that's the one condition
    under which a bounded judge (see `bounded.judge`) should be invoked at
    all. If there's nothing to enrich with, or nothing missing, the judge
    is skipped entirely; authority stays in code.
    """

    primary: Source | None
    secondary: tuple[Source, ...]
    missing_fields: tuple[str, ...]
    complete: bool


def missing_fields(text: str, field_keywords: dict[str, list[str]]) -> list[str]:
    """Return field names whose keyword set has no match anywhere in `text`.

    A cheap, deterministic coverage check -- not a claim that a field is
    *correct*, only that the primary source doesn't obviously address it.
    """
    lowered = text.lower()
    return [
        field
        for field, keywords in field_keywords.items()
        if not any(keyword.lower() in lowered for keyword in keywords)
    ]


def select(sources: list[Source], field_keywords: dict[str, list[str]]) -> Selection:
    """Deterministically pick one primary source and rank the rest as secondary.

    `sources` must already be ordered by authority (e.g. official website >
    LinkedIn > search) -- this function does not judge which source is more
    trustworthy, only which of the *valid* ones came first. The first valid,
    non-empty source wins as primary; every other valid source becomes
    secondary, available for the judge to draw from but never blended in
    automatically.
    """
    valid_sources = [s for s in sources if s.valid and s.text]

    if not valid_sources:
        return Selection(primary=None, secondary=(), missing_fields=(), complete=False)

    primary, *secondary = valid_sources
    missing = tuple(missing_fields(primary.text, field_keywords)) if primary.text else ()
    complete = not (secondary and missing)

    return Selection(
        primary=primary,
        secondary=tuple(secondary),
        missing_fields=missing,
        complete=complete,
    )
