from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass(frozen=True)
class Capability[TIn: BaseModel, TOut: BaseModel]:
    """A single typed unit of work: one input model in, one output model out.

    Registering a Capability once (see `bounded.registry`) makes it runnable
    as a CLI subcommand, a LangGraph node, or an MCP tool (see
    `bounded.adapters`) without rewriting the logic for each surface. The
    logic itself never knows which surface is calling it.
    """

    name: str
    description: str
    input_model: type[TIn]
    output_model: type[TOut]
    run: Callable[[TIn], TOut]

    def __call__(self, input_value: TIn) -> TOut:
        return self.run(input_value)
