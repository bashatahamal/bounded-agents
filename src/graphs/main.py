from langgraph.graph import START, StateGraph, END

from graphs.nodes.fetcher import fetch_linkedin, fetch_search, fetch_website
from graphs.nodes.judge import build_structured_input, judge_node, need_judge
from graphs.nodes.summarizer import summarize
from graphs.nodes.validation import select_primary_and_secondary, validate_sources
from graphs.states.research import ResearchState

graph = StateGraph(ResearchState)

# -----------------------
# Nodes
# -----------------------
graph.add_node("fetch_website", fetch_website)
graph.add_node("fetch_linkedin", fetch_linkedin)
graph.add_node("fetch_search", fetch_search)

graph.add_node("validate", validate_sources)
graph.add_node("select_sources", select_primary_and_secondary)
graph.add_node("judge", judge_node)
graph.add_node("build_input", build_structured_input)
graph.add_node("summarize", summarize)

# -----------------------
# START → parallel fetch
# -----------------------
graph.add_edge(START, "fetch_website")
graph.add_edge(START, "fetch_linkedin")
graph.add_edge(START, "fetch_search")

# -----------------------
# Fan-in: wait for ALL fetches
# -----------------------
graph.add_edge("fetch_website", "validate")
graph.add_edge("fetch_linkedin", "validate")
graph.add_edge("fetch_search", "validate")

# -----------------------
# Sequential processing
# -----------------------
graph.add_edge("validate", "select_sources")

graph.add_conditional_edges(
    "select_sources",
    need_judge,
    {
        True: "judge",
        False: "build_input",
    },
)

graph.add_edge("judge", "build_input")
graph.add_edge("build_input", "summarize")
graph.add_edge("summarize", END)


# 🔑 REQUIRED for LangGraph
graph = graph.compile()