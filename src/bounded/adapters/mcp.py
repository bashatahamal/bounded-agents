from __future__ import annotations

from typing import Any

from bounded.capability import Capability


def as_mcp_tool(capability: Capability) -> dict[str, Any]:
    """Describe a Capability as an MCP tool definition: name, description,
    JSON schemas, and a handler -- ready to register with any MCP server
    implementation.

    This returns a plain dict rather than depending on a specific MCP SDK,
    so `bounded` doesn't force that dependency on projects that only want
    the CLI or LangGraph surface. Wire it up with, e.g., FastMCP:

        tool = as_mcp_tool(my_capability)
        mcp_server.add_tool(
            tool["handler"], name=tool["name"], description=tool["description"]
        )
    """

    def handler(**kwargs: Any) -> Any:
        input_value = capability.input_model(**kwargs)
        result = capability.run(input_value)
        return result.model_dump()

    return {
        "name": capability.name,
        "description": capability.description,
        "input_schema": capability.input_model.model_json_schema(),
        "output_schema": capability.output_model.model_json_schema(),
        "handler": handler,
    }
