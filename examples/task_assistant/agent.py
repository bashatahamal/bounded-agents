from __future__ import annotations

from pathlib import Path

from bounded.agent import Agent
from bounded.context import ContextSource, build_context_pack
from bounded.llm.openai_provider import OpenAIProvider
from bounded.memory import JsonlMemoryStore
from task_assistant.settings import get_settings
from task_assistant.store import TaskStore
from task_assistant.tools import build_tools

DATA_DIR = Path(__file__).parent / "data"
TASKS_PATH = DATA_DIR / "tasks.json"
MEMORY_PATH = DATA_DIR / "memory.jsonl"

SYSTEM_PROMPT_TEMPLATE = """You are a task assistant. You help the user track tasks and \
remember their preferences across conversations.

Use the tools available to you for every task-related request -- never claim you added,
listed, or completed a task without actually calling the corresponding tool. If the user
asks you to remember something, call remember_preference; don't just say you will.

{memory_section}"""


def _build_system_prompt(memory: JsonlMemoryStore) -> str:
    entries = memory.list()
    # Already provenance-ranked by .list() -- priority = rank order, so a
    # tight max_chars budget keeps the most-trusted facts first.
    sources = [
        ContextSource(name=f"memory-{i}", content=f"- {entry.content}", priority=i)
        for i, entry in enumerate(entries)
    ]
    pack = build_context_pack(sources, max_chars=2000)

    if pack:
        memory_section = f"What you remember about the user:\n\n{pack}"
    else:
        memory_section = "You don't have any remembered preferences yet."

    return SYSTEM_PROMPT_TEMPLATE.format(memory_section=memory_section)


def build_agent() -> Agent:
    settings = get_settings()
    store = TaskStore(TASKS_PATH)
    memory = JsonlMemoryStore(MEMORY_PATH)
    tools = build_tools(store, memory)

    llm = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    return Agent(llm=llm, tools=tools, system_prompt=_build_system_prompt(memory))
