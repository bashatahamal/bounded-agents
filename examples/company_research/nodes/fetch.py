from __future__ import annotations

from langchain_core.prompts import PromptTemplate

from company_research import fetchers
from company_research.llm_client import get_llm_client
from company_research.prompts import get_prompts
from company_research.state import ResearchState, SearchResult


def fetch_website(state: ResearchState) -> dict:
    try:
        return {"website_text": fetchers.crawl_official_website(state["company_name"])}
    except Exception as e:
        return {"website_text": None, "errors": [f"Website fetch failed: {e}"]}


def fetch_linkedin(state: ResearchState) -> dict:
    try:
        return {"linkedin_text": fetchers.fetch_linkedin_snippet(state["company_name"])}
    except Exception as e:
        return {"linkedin_text": None, "errors": [f"LinkedIn fetch failed: {e}"]}


def fetch_search(state: ResearchState) -> dict:
    try:
        return {"results": fetchers.fetch_search_snippets(state["company_name"])}
    except Exception as e:
        return {"results": None, "errors": [f"Search fetch failed: {e}"]}


def _run_search_prompt(prompt_name: str, search_result: str | None) -> str:
    template = PromptTemplate(
        template=get_prompts()[prompt_name], input_variables=["search_result"]
    )
    return get_llm_client().complete(user_input=template.format(search_result=search_result))


def search_general(state: SearchResult) -> dict:
    return {"search_general": _run_search_prompt("search_general", state["results"])}


def search_founder(state: SearchResult) -> dict:
    return {"search_founder": _run_search_prompt("search_founder", state["results"])}


def search_finance(state: SearchResult) -> dict:
    return {"search_finance": _run_search_prompt("search_finance", state["results"])}


def search_news(state: SearchResult) -> dict:
    return {"search_news": _run_search_prompt("search_news", state["results"])}
