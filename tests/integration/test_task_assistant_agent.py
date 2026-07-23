import task_assistant.agent as agent_module
from task_assistant.agent import build_agent
from task_assistant.store import TaskStore

from bounded.llm.base import ChatResult, ToolCallRequest


class _ScriptedLLM:
    """Same spirit as tests/unit/test_agent.py's stub -- no network involved."""

    def __init__(self, script: list[ChatResult]):
        self.script = list(script)

    def chat(self, messages, tools):
        return self.script.pop(0)


def _redirect_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_module, "TASKS_PATH", tmp_path / "tasks.json")
    monkeypatch.setattr(agent_module, "MEMORY_PATH", tmp_path / "memory.jsonl")


def test_build_agent_wires_all_four_tools(tmp_path, monkeypatch):
    _redirect_data_dir(monkeypatch, tmp_path)

    agent = build_agent()

    assert set(agent.tools_by_name) == {
        "add_task",
        "list_tasks",
        "complete_task",
        "remember_preference",
    }


def test_end_to_end_add_task_conversation(tmp_path, monkeypatch):
    _redirect_data_dir(monkeypatch, tmp_path)
    agent = build_agent()
    add_task_call = ToolCallRequest(id="c1", name="add_task", arguments={"title": "buy milk"})
    agent.llm = _ScriptedLLM(
        [
            ChatResult(content=None, tool_calls=[add_task_call]),
            ChatResult(content='Added "buy milk" to your tasks.', tool_calls=[]),
        ]
    )

    thread = agent.run("add a task to buy milk")

    assert thread.final_answer == 'Added "buy milk" to your tasks.'
    assert thread.stopped_reason == "answered"
    assert thread.tool_calls[0].tool_name == "add_task"
    assert thread.tool_calls[0].error is None
    assert thread.tool_calls[0].output["title"] == "buy milk"

    # Actually persisted, not just returned in the tool result.
    store = TaskStore(tmp_path / "tasks.json")
    assert [t.title for t in store.list()] == ["buy milk"]


def test_remembered_preference_appears_in_a_freshly_built_agents_prompt(tmp_path, monkeypatch):
    _redirect_data_dir(monkeypatch, tmp_path)

    first_agent = build_agent()
    first_agent.llm = _ScriptedLLM(
        [
            ChatResult(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="c1",
                        name="remember_preference",
                        arguments={"text": "checks tasks in the evening"},
                    )
                ],
            ),
            ChatResult(content="Got it, I'll remember that.", tool_calls=[]),
        ]
    )
    first_agent.run("remember that i check tasks in the evening")

    # A brand-new agent build (e.g. next process start) should see it in its
    # Context Pack -- proves memory -> ContextSource -> system_prompt wiring.
    second_agent = build_agent()

    assert "checks tasks in the evening" in second_agent.system_prompt
