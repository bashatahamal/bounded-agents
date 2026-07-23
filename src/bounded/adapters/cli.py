from __future__ import annotations

import argparse
from typing import Any

from pydantic import BaseModel

from bounded.capability import Capability


def add_capability_subcommand(
    subparsers: argparse._SubParsersAction,
    capability: Capability[BaseModel, BaseModel],
) -> None:
    """Register a Capability as an argparse subcommand.

    Each field on the capability's input model becomes a CLI flag; fields
    with no default become required flags. Attach the returned subparser's
    namespace to `run_from_namespace` to actually execute it.
    """
    parser = subparsers.add_parser(capability.name, help=capability.description)

    for field_name, field_info in capability.input_model.model_fields.items():
        flag = f"--{field_name.replace('_', '-')}"
        kwargs: dict[str, Any] = {"dest": field_name}
        if field_info.is_required():
            kwargs["required"] = True
        else:
            kwargs["default"] = field_info.default
        if field_info.description:
            kwargs["help"] = field_info.description
        parser.add_argument(flag, **kwargs)

    parser.set_defaults(_capability=capability)


def run_from_namespace(
    capability: Capability[BaseModel, BaseModel],
    namespace: argparse.Namespace,
) -> BaseModel:
    """Build the capability's input model from parsed CLI args and run it."""
    field_names = capability.input_model.model_fields.keys()
    kwargs = {name: getattr(namespace, name) for name in field_names}
    input_value = capability.input_model(**kwargs)
    return capability.run(input_value)
