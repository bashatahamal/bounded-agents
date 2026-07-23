from __future__ import annotations

from typing import Protocol

Cell = str | int | float


class Sink(Protocol):
    """Anything that can receive rows of structured output.

    `destination` names where within the sink's backing store the rows go
    -- a worksheet name for Sheets, a table/file stem for CSV or JSONL.
    Swapping sinks (Sheets in production, CSV in a quick local run) never
    touches pipeline logic.
    """

    def write(self, columns: list[str], rows: list[list[Cell]], *, destination: str) -> None: ...
