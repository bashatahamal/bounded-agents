from langgraph.graph import START, StateGraph, END

from graphs.nodes.fetcher import fetch_linkedin, fetch_search, fetch_website, search_finance, search_founder, search_general, search_news
from graphs.nodes.judge import build_structured_input, judge_node, need_judge
from graphs.nodes.summarizer import summarize
from graphs.nodes.validation import select_primary_and_secondary, validate_sources, reason_and_summarize, aggregate_inputs
from graphs.states.research import ResearchState

graph = StateGraph(ResearchState)

# -----------------------
# Nodes
# -----------------------
graph.add_node("fetch_website", fetch_website)
graph.add_node("fetch_linkedin", fetch_linkedin)
graph.add_node("fetch_search", fetch_search)

# graph.add_node("validate", validate_sources)
# graph.add_node("select_sources", select_primary_and_secondary)
# graph.add_node("judge", judge_node)
# graph.add_node("build_input", build_structured_input)
# graph.add_node("summarize", summarize)

graph.add_node("search_general", search_general)
graph.add_node("search_finance", search_finance)
graph.add_node("search_founder", search_founder)
graph.add_node("search_news", search_news)


graph.add_node("aggregate_inputs", aggregate_inputs)

# Single terminal reasoning node
graph.add_node("reason_and_summarize", reason_and_summarize)

# -----------------------
# START → parallel fetch
# -----------------------
graph.add_edge(START, "fetch_website")
graph.add_edge(START, "fetch_linkedin")
graph.add_edge(START, "fetch_search")

# -----------------------
# Fan-in: wait for ALL fetches
# -----------------------
graph.add_edge("fetch_website", "aggregate_inputs")
graph.add_edge("fetch_linkedin", "aggregate_inputs")


graph.add_edge("fetch_search", "search_general")
graph.add_edge("fetch_search", "search_founder")
graph.add_edge("fetch_search", "search_finance")
graph.add_edge("fetch_search", "search_news")


# graph.add_edge("search_general", "validate")
# graph.add_edge("search_founder", "validate")
# graph.add_edge("search_finance", "validate")
# graph.add_edge("search_news", "validate")


# graph.add_edge("validate", END)



graph.add_edge("search_general", "aggregate_inputs")
graph.add_edge("search_founder", "aggregate_inputs")
graph.add_edge("search_finance", "aggregate_inputs")
graph.add_edge("search_news", "aggregate_inputs")

# -----------------------
# Terminal reasoning
# -----------------------
graph.add_edge("aggregate_inputs", "reason_and_summarize")
graph.add_edge("reason_and_summarize", END)


# -----------------------
# Sequential processing
# -----------------------
# graph.add_edge("validate", "select_sources")

# graph.add_conditional_edges(
#     "select_sources",
#     need_judge,
#     {
#         True: "judge",
#         False: "build_input",
#     },
# )

# graph.add_edge("judge", "build_input")
# graph.add_edge("build_input", "summarize")
# graph.add_edge("summarize", END)


# 🔑 REQUIRED for LangGraph
graph = graph.compile()