from __future__ import annotations

from langchain_core.prompts import PromptTemplate

from company_research.llm_client import get_llm_client
from company_research.prompts import get_prompts
from company_research.state import ResearchState


def summarize(state: ResearchState) -> dict:
    if state.get("summarized"):
        return {}

    structured = state.get("structured_input")
    if not structured or not state.get("valid_summary", False):
        return {}

    template = PromptTemplate(
        template=get_prompts()["final_summarizer"], input_variables=["structured_input"]
    )
    result = get_llm_client().complete(user_input=template.format(structured_input=structured))
    return {"summary": result.strip(), "summarized": True}
