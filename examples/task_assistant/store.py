from __future__ import annotations

import json
import secrets
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class Task:
    id: str
    title: str
    due: str | None
    done: bool
    created_at: str


class TaskStore:
    """JSON-file-backed task list: load-all/rewrite-all on write, the same
    shape as `bounded.memory.JsonlMemoryStore` and `bounded.sinks.jsonl`.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _load(self) -> list[Task]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Task(**item) for item in raw.get("tasks", [])]

    def _save(self, tasks: list[Task]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump({"tasks": [asdict(t) for t in tasks]}, f, indent=2)
        tmp.replace(self.path)

    def add(self, title: str, due: str | None = None) -> Task:
        task = Task(
            id=secrets.token_hex(4),
            title=title.strip(),
            due=due,
            done=False,
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._lock:
            tasks = self._load()
            tasks.append(task)
            self._save(tasks)
        return task

    def list(self, include_done: bool = True) -> list[Task]:
        tasks = self._load()
        if not include_done:
            tasks = [t for t in tasks if not t.done]
        return tasks

    def complete(self, task_id: str) -> Task | None:
        with self._lock:
            tasks = self._load()
            for task in tasks:
                if task.id == task_id:
                    task.done = True
                    self._save(tasks)
                    return task
        return None
