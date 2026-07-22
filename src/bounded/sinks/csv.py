from __future__ import annotations

import csv
from pathlib import Path

from bounded.sinks.base import Cell


class CsvSink:
    """Writes rows to `{base_dir}/{destination}.csv`, appending across calls."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, columns: list[str], rows: list[list[Cell]], *, destination: str) -> None:
        path = self.base_dir / f"{destination}.csv"
        is_new = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(columns)
            writer.writerows(rows)
