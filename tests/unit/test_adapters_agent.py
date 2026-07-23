from pydantic import BaseModel

from bounded.adapters.agent import as_openai_tool
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


def test_as_openai_tool_shape():
    tool = as_openai_tool(double_capability)

    assert tool["type"] == "function"
    assert tool["function"]["name"] == "double"
    assert tool["function"]["description"] == "doubles x"
    assert tool["function"]["parameters"]["properties"]["x"]["type"] == "integer"
