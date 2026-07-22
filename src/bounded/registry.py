from __future__ import annotations

from bounded.capability import Capability


class Registry:
    """In-process lookup for registered Capabilities, keyed by name."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> Capability:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability '{capability.name}' is already registered")
        self._capabilities[capability.name] = capability
        return capability

    def get(self, name: str) -> Capability:
        try:
            return self._capabilities[name]
        except KeyError:
            raise KeyError(
                f"No capability registered as '{name}'. Known: {sorted(self._capabilities)}"
            ) from None

    def list(self) -> list[Capability]:
        return list(self._capabilities.values())


registry = Registry()
