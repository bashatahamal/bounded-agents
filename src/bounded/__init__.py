"""bounded — deterministic orchestration for LLM pipelines.

Authority lives in code; phrasing lives in the LLM. See docs/DESIGN.md.
"""

from bounded.capability import Capability
from bounded.registry import Registry, registry

__all__ = ["Capability", "Registry", "registry"]

__version__ = "0.3.1"
