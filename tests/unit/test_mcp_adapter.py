from pydantic import BaseModel

from bounded.adapters.mcp import as_mcp_tool
from bounded.capability import Capability


class In(BaseModel):
    x: int


class Out(BaseModel):
    y: int


double_capability = Capability(
    name="double",
    description="doubles x",
    input_model=In,
    output_model=Out,
    run=lambda i: Out(y=i.x * 2),
)


def test_as_mcp_tool_exposes_name_description_and_schemas():
    tool = as_mcp_tool(double_capability)

    assert tool["name"] == "double"
    assert tool["description"] == "doubles x"
    assert tool["input_schema"]["properties"]["x"]["type"] == "integer"
    assert tool["output_schema"]["properties"]["y"]["type"] == "integer"


def test_as_mcp_tool_handler_runs_the_capability_and_returns_a_dict():
    tool = as_mcp_tool(double_capability)

    result = tool["handler"](x=21)

    assert result == {"y": 42}
