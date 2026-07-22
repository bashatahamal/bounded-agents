from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def load_json_credentials(value: str) -> dict[str, Any]:
    """Load a JSON credentials blob from a file path, base64 string, or raw JSON.

    Tries, in order: a path to a JSON file on disk, a base64-encoded JSON
    string, then a raw JSON string. Always returns a dict or raises
    ValueError -- never silently returns `{}`, so a misconfigured credential
    fails loudly at startup instead of surfacing as a confusing auth error
    later.
    """
    candidate = value.strip()

    path = Path(candidate)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        decoded = base64.b64decode(candidate, validate=True).decode("utf-8")
        parsed = json.loads(decoded)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse credentials as a file path, base64, or raw JSON: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Credentials must decode to a JSON object, got {type(parsed).__name__}")

    return parsed
