from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from bounded.capability import Capability


def safe_merge(a: Any, b: Any) -> Any:
    """Generic LangGraph state-merge reducer: None-safe, type-aware, deterministic.

    Lists concatenate; dicts shallow-merge (`b` wins on key conflicts);
    everything else (bools, strings, numbers) is last-write-wins. Use it as
    the reducer in `Annotated[T, safe_merge]` state fields so parallel graph
    branches merge into shared state predictably instead of raising
    "concurrent update" errors.
    """
    if a is None:
        return b
    if b is None:
        return a
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    if isinstance(a, dict) and isinstance(b, dict):
        merged = dict(a)
        merged.update(b)
        return merged
    return b


def as_langgraph_node[TIn: BaseModel, TOut: BaseModel](
    capability: Capability[TIn, TOut],
    *,
    from_state: Callable[[dict], TIn],
    to_state: Callable[[TOut], dict],
) -> Callable[[dict], dict]:
    """Wrap a Capability as a LangGraph node function: dict state -> dict update.

    `from_state` pulls the capability's typed input out of the graph state;
    `to_state` turns the typed output back into a partial state update. The
    capability's own logic never touches the graph's dict shape, so the same
    capability can run outside a graph (CLI, MCP tool) unchanged.
    """

    def node(state: dict) -> dict:
        result = capability.run(from_state(state))
        return to_state(result)

    node.__name__ = f"node__{capability.name}"
    return node
