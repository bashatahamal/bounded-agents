from __future__ import annotations

from typing import Any

from bounded.capability import Capability


def as_openai_tool(capability: Capability) -> dict[str, Any]:
    """Describe a Capability as an OpenAI tool-calling schema.

    Mirrors `bounded.adapters.mcp.as_mcp_tool`'s schema extraction, just in
    the wire shape OpenAI's `tools=[...]` parameter expects. `bounded.agent.Agent`
    uses this internally; exposed publicly for the same reason `as_mcp_tool`
    is -- so a caller can drive Capabilities through their own loop.
    """
    return {
        "type": "function",
        "function": {
            "name": capability.name,
            "description": capability.description,
            "parameters": capability.input_model.model_json_schema(),
        },
    }
