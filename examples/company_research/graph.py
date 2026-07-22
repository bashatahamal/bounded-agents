from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from company_research.nodes.fetch import (
    fetch_linkedin,
    fetch_search,
    fetch_website,
    search_finance,
    search_founder,
    search_general,
    search_news,
)
from company_research.nodes.judge_node import build_structured_input, judge_node, need_judge
from company_research.nodes.summarize import summarize
from company_research.nodes.validate import select_primary_and_secondary, validate_sources
from company_research.state import ResearchState

_builder = StateGraph(ResearchState)

# -----------------------
# Nodes
# -----------------------
_builder.add_node("fetch_website", fetch_website)
_builder.add_node("fetch_linkedin", fetch_linkedin)
_builder.add_node("fetch_search", fetch_search)

_builder.add_node("validate", validate_sources)
_builder.add_node("select_sources", select_primary_and_secondary)
_builder.add_node("judge", judge_node)
_builder.add_node("build_input", build_structured_input)
_builder.add_node("summarize", summarize)

_builder.add_node("search_general", search_general)
_builder.add_node("search_finance", search_finance)
_builder.add_node("search_founder", search_founder)
_builder.add_node("search_news", search_news)

# -----------------------
# START -> parallel fetch
# -----------------------
_builder.add_edge(START, "fetch_website")
_builder.add_edge(START, "fetch_linkedin")
_builder.add_edge(START, "fetch_search")

# -----------------------
# Fan-in: wait for ALL fetches
# -----------------------
_builder.add_edge("fetch_website", "validate")
_builder.add_edge("fetch_linkedin", "validate")

_builder.add_edge("fetch_search", "search_general")
_builder.add_edge("fetch_search", "search_founder")
_builder.add_edge("fetch_search", "search_finance")
_builder.add_edge("fetch_search", "search_news")

_builder.add_edge("search_general", "validate")
_builder.add_edge("search_founder", "validate")
_builder.add_edge("search_finance", "validate")
_builder.add_edge("search_news", "validate")

# -----------------------
# Sequential processing
# -----------------------
_builder.add_edge("validate", "select_sources")

_builder.add_conditional_edges(
    "select_sources",
    need_judge,
    {True: "judge", False: "build_input"},
)

_builder.add_edge("judge", "build_input")
_builder.add_edge("build_input", "summarize")
_builder.add_edge("summarize", END)

graph = _builder.compile()
