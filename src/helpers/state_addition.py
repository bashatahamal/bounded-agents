from typing import Any

def safe_merge(a: Any, b: Any) -> Any:
    """
    Universal LangGraph merge function.
    - None-safe
    - Type-aware
    - Deterministic
    """

    # -------------------------
    # Handle None
    # -------------------------
    if a is None:
        return b
    if b is None:
        return a

    # -------------------------
    # Lists → concatenate
    # -------------------------
    if isinstance(a, list) and isinstance(b, list):
        return a + b

    # -------------------------
    # Dicts → shallow merge (b wins)
    # -------------------------
    if isinstance(a, dict) and isinstance(b, dict):
        merged = dict(a)
        merged.update(b)
        return merged

    # -------------------------
    # Booleans → last write wins
    # -------------------------
    if isinstance(a, bool) and isinstance(b, bool):
        return b

    # -------------------------
    # Strings → last write wins
    # (concatenation is usually wrong semantically)
    # -------------------------
    if isinstance(a, str) and isinstance(b, str):
        return b

    # -------------------------
    # Fallback → last write wins
    # -------------------------
    return b
