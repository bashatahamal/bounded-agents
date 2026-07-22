import pytest
from pydantic import BaseModel

from bounded.capability import Capability
from bounded.registry import Registry


class In(BaseModel):
    x: int


class Out(BaseModel):
    y: int


def _make(name: str) -> Capability[In, Out]:
    return Capability(
        name=name,
        description="doubles x",
        input_model=In,
        output_model=Out,
        run=lambda i: Out(y=i.x * 2),
    )


def test_register_and_get_roundtrip():
    registry = Registry()
    cap = _make("double")
    registry.register(cap)

    assert registry.get("double") is cap


def test_register_rejects_duplicate_names():
    registry = Registry()
    registry.register(_make("double"))

    with pytest.raises(ValueError):
        registry.register(_make("double"))


def test_get_raises_key_error_with_known_names_listed():
    registry = Registry()
    registry.register(_make("double"))

    with pytest.raises(KeyError, match="double"):
        registry.get("missing")


def test_list_returns_all_registered_capabilities():
    registry = Registry()
    registry.register(_make("a"))
    registry.register(_make("b"))

    assert {c.name for c in registry.list()} == {"a", "b"}
