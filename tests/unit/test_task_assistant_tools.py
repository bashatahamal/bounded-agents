from task_assistant.store import TaskStore
from task_assistant.tools import (
    AddTaskIn,
    CompleteTaskIn,
    ListTasksIn,
    RememberIn,
    build_tools,
)

from bounded.memory import JsonlMemoryStore, Provenance


def _tools(tmp_path):
    store = TaskStore(tmp_path / "tasks.json")
    memory = JsonlMemoryStore(tmp_path / "memory.jsonl")
    return {t.name: t for t in build_tools(store, memory)}, store, memory


def test_add_task_creates_and_returns_it(tmp_path):
    tools, store, _ = _tools(tmp_path)

    result = tools["add_task"].run(AddTaskIn(title="buy milk", due="2026-07-23"))

    assert result.title == "buy milk"
    assert result.due == "2026-07-23"
    assert result.done is False
    assert len(store.list()) == 1


def test_list_tasks_excludes_done_by_default(tmp_path):
    tools, store, _ = _tools(tmp_path)
    added = tools["add_task"].run(AddTaskIn(title="task one"))
    store.complete(added.id)
    tools["add_task"].run(AddTaskIn(title="task two"))

    result = tools["list_tasks"].run(ListTasksIn(include_done=False))

    assert [t.title for t in result.tasks] == ["task two"]


def test_list_tasks_include_done_returns_everything(tmp_path):
    tools, store, _ = _tools(tmp_path)
    added = tools["add_task"].run(AddTaskIn(title="task one"))
    store.complete(added.id)
    tools["add_task"].run(AddTaskIn(title="task two"))

    result = tools["list_tasks"].run(ListTasksIn(include_done=True))

    assert {t.title for t in result.tasks} == {"task one", "task two"}


def test_complete_task_marks_it_done(tmp_path):
    tools, store, _ = _tools(tmp_path)
    added = tools["add_task"].run(AddTaskIn(title="task one"))

    result = tools["complete_task"].run(CompleteTaskIn(task_id=added.id))

    assert result.completed is True
    assert store.list(include_done=True)[0].done is True


def test_complete_task_unknown_id_reports_not_completed(tmp_path):
    tools, _, _ = _tools(tmp_path)

    result = tools["complete_task"].run(CompleteTaskIn(task_id="does-not-exist"))

    assert result.completed is False


def test_remember_preference_writes_with_human_manual_provenance(tmp_path):
    tools, _, memory = _tools(tmp_path)

    result = tools["remember_preference"].run(RememberIn(text="checks tasks in the evening"))

    assert result.remembered == "checks tasks in the evening"
    entries = memory.list(scope="preferences")
    assert len(entries) == 1
    assert entries[0].provenance == Provenance.HUMAN_MANUAL
