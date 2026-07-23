from pydantic import BaseModel

from bounded.agent import Agent, ScopeError
from bounded.capability import Capability
from bounded.llm.base import ChatResult, ToolCallRequest, image_message_content


class AddIn(BaseModel):
    a: int
    b: int


class AddOut(BaseModel):
    sum: int


def _add(input_value: AddIn) -> AddOut:
    return AddOut(sum=input_value.a + input_value.b)


add_capability = Capability(
    name="add",
    description="add two numbers",
    input_model=AddIn,
    output_model=AddOut,
    run=_add,
)


class _ScriptedLLM:
    """Fake ToolCallingLLM returning a pre-scripted sequence of ChatResults,
    one per call -- same spirit as test_judge.py's _StubLLM, no network."""

    def __init__(self, script: list[ChatResult]):
        self.script = list(script)
        self.calls: list[tuple[list[dict], list[dict]]] = []

    def chat(self, messages, tools):
        self.calls.append((messages, tools))
        return self.script.pop(0)


def _tool_call(name: str, arguments: dict, call_id: str = "call_1") -> ChatResult:
    request = ToolCallRequest(id=call_id, name=name, arguments=arguments)
    return ChatResult(content=None, tool_calls=[request])


def _final(text: str) -> ChatResult:
    return ChatResult(content=text, tool_calls=[])


def test_agent_runs_a_tool_then_answers():
    llm = _ScriptedLLM([_tool_call("add", {"a": 2, "b": 3}), _final("The sum is 5.")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="You are a calculator.")

    thread = agent.run("what is 2 + 3?")

    assert thread.final_answer == "The sum is 5."
    assert thread.stopped_reason == "answered"
    assert len(thread.tool_calls) == 1
    assert thread.tool_calls[0].output == {"sum": 5}
    assert thread.tool_calls[0].error is None


def test_agent_stops_at_step_limit_instead_of_looping_forever():
    always_call_tool = [_tool_call("add", {"a": 1, "b": 1}, call_id=f"call_{i}") for i in range(20)]
    llm = _ScriptedLLM(always_call_tool)
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="loop", max_steps=3)

    thread = agent.run("loop forever")

    assert thread.stopped_reason == "step_limit"
    assert len(thread.tool_calls) == 3
    assert "step limit" in thread.final_answer.lower()


def test_agent_guard_rejection_becomes_a_tool_error_not_a_crash():
    def reject_everything(capability, input_value):
        raise ScopeError("not allowed in this scope")

    llm = _ScriptedLLM([_tool_call("add", {"a": 1, "b": 1}), _final("done")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="guarded", guard=reject_everything)

    thread = agent.run("try it")

    assert thread.tool_calls[0].error == "not allowed in this scope"
    assert thread.tool_calls[0].output is None
    assert thread.stopped_reason == "answered"  # loop continued after the rejection


def test_agent_unknown_tool_name_becomes_a_tool_error():
    llm = _ScriptedLLM([_tool_call("does_not_exist", {}), _final("done")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="x")

    thread = agent.run("try unknown")

    assert "Unknown tool" in thread.tool_calls[0].error


def test_agent_tool_exception_becomes_a_tool_error_not_a_crash():
    def _boom(input_value: AddIn) -> AddOut:
        raise RuntimeError("kaboom")

    boom_capability = Capability(
        name="add", description="broken", input_model=AddIn, output_model=AddOut, run=_boom
    )
    llm = _ScriptedLLM([_tool_call("add", {"a": 1, "b": 1}), _final("done")])
    agent = Agent(llm=llm, tools=[boom_capability], system_prompt="x")

    thread = agent.run("try it")

    assert thread.tool_calls[0].error == "kaboom"
    assert thread.final_answer == "done"


def test_agent_invalid_arguments_become_a_tool_error():
    llm = _ScriptedLLM([_tool_call("add", {"a": "not-a-number"}), _final("done")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="x")

    thread = agent.run("try it")

    assert thread.tool_calls[0].error is not None
    assert thread.tool_calls[0].output is None


def test_agent_continues_an_existing_thread_across_turns():
    llm = _ScriptedLLM([_final("first answer"), _final("second answer")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="x")

    thread = agent.run("first question")
    thread = agent.run("second question", thread=thread)

    assert thread.final_answer == "second answer"
    # both user turns are preserved in message history
    user_messages = [m["content"] for m in thread.messages if m["role"] == "user"]
    assert user_messages == ["first question", "second question"]


def test_agent_accepts_multimodal_content_as_user_input():
    llm = _ScriptedLLM([_final("that's a cat")])
    agent = Agent(llm=llm, tools=[add_capability], system_prompt="x")
    content = image_message_content("what is this?", "data:image/jpeg;base64,abc123")

    thread = agent.run(content)

    assert thread.final_answer == "that's a cat"
    user_message = next(m for m in thread.messages if m["role"] == "user")
    assert user_message["content"] == content
    # exactly what reached the LLM -- bounded never inspects or reshapes it.
    # (llm.calls[0] aliases thread.messages itself, which gains the
    # assistant's reply after this call returns, so look up by role rather
    # than by a now-stale trailing index.)
    sent_messages, _ = llm.calls[0]
    sent_user_message = next(m for m in sent_messages if m["role"] == "user")
    assert sent_user_message["content"] == content
