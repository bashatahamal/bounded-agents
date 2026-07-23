from __future__ import annotations

from pydantic import BaseModel, Field

from bounded.capability import Capability
from bounded.memory import MemoryStore, Provenance
from task_assistant.store import TaskStore


class AddTaskIn(BaseModel):
    title: str = Field(..., description="short task title")
    due: str | None = Field(None, description="due date, e.g. 2026-07-25, or omit if none")


class TaskOut(BaseModel):
    id: str
    title: str
    due: str | None
    done: bool


class ListTasksIn(BaseModel):
    include_done: bool = Field(False, description="include already-completed tasks")


class TaskListOut(BaseModel):
    tasks: list[TaskOut]


class CompleteTaskIn(BaseModel):
    task_id: str = Field(..., description="id of the task to mark done")


class CompleteTaskOut(BaseModel):
    id: str
    completed: bool


class RememberIn(BaseModel):
    text: str = Field(..., description="a preference or fact to remember about how the user works")


class RememberOut(BaseModel):
    remembered: str


def build_tools(store: TaskStore, memory: MemoryStore) -> list[Capability]:
    """Wire a TaskStore + MemoryStore into the four Capabilities the agent
    can call. Each is a plain typed function -- nothing here knows it's
    being driven by an LLM tool-calling loop rather than a CLI or a test.
    """

    def _add_task(input_value: AddTaskIn) -> TaskOut:
        task = store.add(input_value.title, input_value.due)
        return TaskOut(id=task.id, title=task.title, due=task.due, done=task.done)

    def _list_tasks(input_value: ListTasksIn) -> TaskListOut:
        tasks = store.list(include_done=input_value.include_done)
        return TaskListOut(
            tasks=[TaskOut(id=t.id, title=t.title, due=t.due, done=t.done) for t in tasks]
        )

    def _complete_task(input_value: CompleteTaskIn) -> CompleteTaskOut:
        task = store.complete(input_value.task_id)
        return CompleteTaskOut(id=input_value.task_id, completed=task is not None)

    def _remember(input_value: RememberIn) -> RememberOut:
        # A user explicitly asking to be remembered is HUMAN_MANUAL provenance
        # -- the highest rank. An LLM inferring a preference on its own would
        # go through bounded.memory.distill() instead, tagged LLM_INFERRED.
        entry = memory.add("preferences", input_value.text, Provenance.HUMAN_MANUAL)
        return RememberOut(remembered=entry.content)

    return [
        Capability(
            name="add_task",
            description="Add a new task, optionally with a due date.",
            input_model=AddTaskIn,
            output_model=TaskOut,
            run=_add_task,
        ),
        Capability(
            name="list_tasks",
            description="List tasks, optionally including completed ones.",
            input_model=ListTasksIn,
            output_model=TaskListOut,
            run=_list_tasks,
        ),
        Capability(
            name="complete_task",
            description="Mark a task as done by its id.",
            input_model=CompleteTaskIn,
            output_model=CompleteTaskOut,
            run=_complete_task,
        ),
        Capability(
            name="remember_preference",
            description="Remember a user preference or fact for future conversations.",
            input_model=RememberIn,
            output_model=RememberOut,
            run=_remember,
        ),
    ]
