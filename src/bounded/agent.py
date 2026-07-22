from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from bounded.adapters.agent import as_openai_tool
from bounded.capability import Capability
from bounded.llm.base import ChatResult, ToolCallingLLM, ToolCallRequest


class ScopeError(Exception):
    """Raised by a caller-supplied guard to reject a tool call in code.

    The Agent loop catches this and feeds an error message back to the LLM
    instead of crashing or silently allowing the call -- the same "can't
    touch what you don't have open" enforcement pattern, generalized.
    """


@dataclass
class ToolCall:
    """One tool invocation and its outcome -- the audit-trail unit."""

    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    error: str | None


@dataclass
class Thread:
    """A conversation's full state: message history plus every tool call
    ever made in it, across however many `Agent.run()` turns. Nothing here
    is ever silently discarded -- that's what makes the agent auditable.
    """

    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    final_answer: str = ""
    stopped_reason: str = ""


Guard = Callable[[Capability, BaseModel], None]


class Agent:
    """An LLM-driven tool-calling loop: the LLM decides which Capability to
    call, when, and how many times. This is the one place in `bounded`
    where the LLM controls flow -- everywhere else (arbitration, judge)
    authority stays in code. The loop itself stays bounded: a hard step
    limit so it can never run forever, an optional scope `guard` that runs
    in code before every tool call, and every tool failure (bad arguments,
    an unknown tool name, the tool's own exception) captured as a
    `ToolCall.error` instead of ever propagating and crashing the
    conversation.
    """

    def __init__(
        self,
        llm: ToolCallingLLM,
        tools: list[Capability],
        system_prompt: str,
        max_steps: int = 8,
        guard: Guard | None = None,
    ) -> None:
        self.llm = llm
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.tool_schemas = [as_openai_tool(tool) for tool in tools]
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.guard = guard

    def run(self, user_input: str, thread: Thread | None = None) -> Thread:
        """Run one user turn to completion: possibly several tool calls,
        ending either in a text answer or a step-limit cutoff. Pass a prior
        `Thread` back in to continue the same conversation; omit it to
        start a new one.
        """
        if thread is None:
            thread = Thread(messages=[{"role": "system", "content": self.system_prompt}])
        thread.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_steps):
            result = self.llm.chat(thread.messages, self.tool_schemas)

            if not result.tool_calls:
                thread.messages.append({"role": "assistant", "content": result.content or ""})
                thread.final_answer = result.content or ""
                thread.stopped_reason = "answered"
                return thread

            thread.messages.append(_assistant_tool_call_message(result))

            for call in result.tool_calls:
                tool_call = self._execute(call)
                thread.tool_calls.append(tool_call)
                thread.messages.append(_tool_result_message(call, tool_call))

        thread.final_answer = "Stopping to avoid a runaway loop -- step limit reached."
        thread.stopped_reason = "step_limit"
        thread.messages.append({"role": "assistant", "content": thread.final_answer})
        return thread

    def _execute(self, call: ToolCallRequest) -> ToolCall:
        capability = self.tools_by_name.get(call.name)
        if capability is None:
            return ToolCall(
                tool_name=call.name,
                input=call.arguments,
                output=None,
                error=f"Unknown tool '{call.name}'",
            )

        try:
            input_value = capability.input_model(**call.arguments)
            if self.guard is not None:
                self.guard(capability, input_value)
            output = capability.run(input_value)
        except ScopeError as exc:
            return ToolCall(tool_name=call.name, input=call.arguments, output=None, error=str(exc))
        except Exception as exc:  # a tool's own failure must never crash the loop
            return ToolCall(tool_name=call.name, input=call.arguments, output=None, error=str(exc))

        return ToolCall(
            tool_name=call.name,
            input=call.arguments,
            output=output.model_dump(),
            error=None,
        )


def _assistant_tool_call_message(result: ChatResult) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": result.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in result.tool_calls
        ],
    }


def _tool_result_message(call: ToolCallRequest, tool_call: ToolCall) -> dict[str, Any]:
    if tool_call.error:
        payload: dict[str, Any] = {"error": tool_call.error}
    else:
        payload = tool_call.output or {}
    return {"role": "tool", "tool_call_id": call.id, "content": json.dumps(payload)}
