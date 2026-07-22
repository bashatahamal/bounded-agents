from __future__ import annotations

import json
from pathlib import Path

from bounded.sinks.base import Cell


class JsonlSink:
    """Appends rows as JSON-lines records to `{base_dir}/{destination}.jsonl`."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, columns: list[str], rows: list[list[Cell]], *, destination: str) -> None:
        path = self.base_dir / f"{destination}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(dict(zip(columns, row, strict=True)), ensure_ascii=False) + "\n")
