from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from bounded.json_repair import clean_json_text, extract_json_object
from bounded.llm.base import LLMProvider


class Provenance(StrEnum):
    """How a memory entry came to exist, ranked by how much it should be
    trusted -- lower rank wins on conflict. Mirrors the rule a real
    feedback-distillation loop needs: what a human explicitly said outranks
    what a human implied outranks what the LLM merely inferred.
    """

    HUMAN_MANUAL = "human_manual"
    HUMAN_FEEDBACK = "human_feedback"
    LLM_INFERRED = "llm_inferred"


_PROVENANCE_RANK: dict[Provenance, int] = {
    Provenance.HUMAN_MANUAL: 0,
    Provenance.HUMAN_FEEDBACK: 1,
    Provenance.LLM_INFERRED: 2,
}


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    scope: str
    content: str
    provenance: Provenance
    created_at: str


class MemoryStore(Protocol):
    def add(self, scope: str, content: str, provenance: Provenance) -> MemoryEntry: ...
    def list(self, scope: str | None = None) -> list[MemoryEntry]: ...


class JsonlMemoryStore:
    """File-backed `MemoryStore`: one JSON object per line, load-all/rewrite-all
    on write -- same shape as `bounded.sinks.jsonl.JsonlSink`.

    Dedup is exact-match on `(scope, content.strip().lower())`. That's a
    known limitation, not a hidden one: two differently-worded statements of
    the same fact will both be kept. Similarity-based dedup would need an
    embedding call, which is real added cost and complexity this default
    doesn't take on.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _load(self) -> list[MemoryEntry]:
        if not self.path.exists():
            return []
        entries = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                entries.append(
                    MemoryEntry(
                        id=raw["id"],
                        scope=raw["scope"],
                        content=raw["content"],
                        provenance=Provenance(raw["provenance"]),
                        created_at=raw["created_at"],
                    )
                )
        return entries

    def _save(self, entries: list[MemoryEntry]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(
                    json.dumps(
                        {
                            "id": entry.id,
                            "scope": entry.scope,
                            "content": entry.content,
                            "provenance": entry.provenance.value,
                            "created_at": entry.created_at,
                        }
                    )
                    + "\n"
                )
        tmp.replace(self.path)

    def add(self, scope: str, content: str, provenance: Provenance) -> MemoryEntry:
        normalized = content.strip()
        dedup_key = (scope, normalized.lower())

        with self._lock:
            entries = self._load()
            for existing in entries:
                if (existing.scope, existing.content.strip().lower()) == dedup_key:
                    return existing

            entry = MemoryEntry(
                id=secrets.token_hex(4),
                scope=scope,
                content=normalized,
                provenance=provenance,
                created_at=datetime.now(UTC).isoformat(),
            )
            entries.append(entry)
            self._save(entries)

        return entry

    def list(self, scope: str | None = None) -> list[MemoryEntry]:
        entries = self._load()
        if scope is not None:
            entries = [e for e in entries if e.scope == scope]
        return sorted(entries, key=lambda e: (_PROVENANCE_RANK[e.provenance], e.created_at))


@dataclass(frozen=True)
class DistilledRule:
    content: str
    scope: str


def distill(
    *,
    llm: LLMProvider,
    prompt: str,
) -> list[DistilledRule]:
    """Ask the LLM to extract durable rules from a prompt the caller has
    already built (feedback text, existing entries, whatever framing is
    needed -- `bounded` doesn't prescribe a template, same as `bounded.judge`).

    Expected output shape: `{"rules": [{"content": "...", "scope": "..."}]}`.
    Reuses the same defensive-parsing discipline as `bounded.judge`: returns
    `[]` rather than raising on unparseable output, since a missed memory
    write is acceptable degradation, never something that should break the
    caller.

    Provenance is deliberately not part of the LLM's output -- only code
    assigns it (callers should tag whatever this returns as
    `Provenance.LLM_INFERRED`; `HUMAN_MANUAL` / `HUMAN_FEEDBACK` come from a
    separate, code-driven path), so the LLM can never claim its own guess is
    more authoritative than it is.
    """
    raw = llm.complete(user_input=prompt)
    text = clean_json_text(raw)

    json_text = extract_json_object(text)
    if not json_text:
        return []

    try:
        parsed = json.loads(json_text, strict=False)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, dict):
        return []

    rules = parsed.get("rules")
    if not isinstance(rules, list):
        return []

    result = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        content = rule.get("content")
        scope = rule.get("scope")
        if (
            isinstance(content, str)
            and content.strip()
            and isinstance(scope, str)
            and scope.strip()
        ):
            result.append(DistilledRule(content=content.strip(), scope=scope.strip()))
    return result
