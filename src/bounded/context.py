from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextSource:
    """One named block of context, in caller-defined priority order.

    `bounded` doesn't decide what goes into a context pack (rules, memory,
    recent activity, ...) -- callers build `ContextSource`s from whatever
    they have. This only decides how to combine them.
    """

    name: str
    content: str
    priority: int  # lower = higher priority, included first, dropped last


def build_context_pack(sources: list[ContextSource], max_chars: int | None = None) -> str:
    """Assemble a single preface string from prioritized context sources.

    Sources are concatenated in priority order. If `max_chars` is set and
    the combined text would exceed it, whole lowest-priority sources are
    dropped first -- never truncated mid-source, so the model never reads a
    block that cuts off mid-sentence.
    """
    ordered = sorted(sources, key=lambda s: s.priority)

    if max_chars is None:
        selected = ordered
    else:
        selected = []
        used = 0
        separator_len = 2  # "\n\n" between blocks
        for source in ordered:
            block_len = len(source.content) + (separator_len if selected else 0)
            if used + block_len > max_chars:
                # This source (and, being sorted by priority, everything
                # lower-priority after it) doesn't fit -- stop here rather
                # than skip ahead, so what's dropped is always a clean
                # lowest-priority tail, not an arbitrary scattered subset.
                break
            selected.append(source)
            used += block_len

    return "\n\n".join(f"## {source.name}\n{source.content}" for source in selected)
