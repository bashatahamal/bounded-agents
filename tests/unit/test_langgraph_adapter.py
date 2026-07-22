from pydantic import BaseModel

from bounded.adapters.langgraph import as_langgraph_node, safe_merge
from bounded.capability import Capability


def test_safe_merge_none_is_identity():
    assert safe_merge(None, "b") == "b"
    assert safe_merge("a", None) == "a"


def test_safe_merge_concatenates_lists():
    assert safe_merge([1, 2], [3]) == [1, 2, 3]


def test_safe_merge_shallow_merges_dicts_b_wins():
    assert safe_merge({"a": 1, "b": 1}, {"b": 2, "c": 3}) == {"a": 1, "b": 2, "c": 3}


def test_safe_merge_last_write_wins_for_scalars():
    assert safe_merge("old", "new") == "new"
    assert safe_merge(True, False) is False


class Greeting(BaseModel):
    name: str


class GreetingResult(BaseModel):
    message: str


def _greet(input_value: Greeting) -> GreetingResult:
    return GreetingResult(message=f"hello {input_value.name}")


greet_capability = Capability(
    name="greet",
    description="say hello",
    input_model=Greeting,
    output_model=GreetingResult,
    run=_greet,
)


def test_as_langgraph_node_wraps_capability_over_dict_state():
    node = as_langgraph_node(
        greet_capability,
        from_state=lambda state: Greeting(name=state["who"]),
        to_state=lambda result: {"greeting": result.message},
    )

    update = node({"who": "world"})

    assert update == {"greeting": "hello world"}
    assert node.__name__ == "node__greet"
