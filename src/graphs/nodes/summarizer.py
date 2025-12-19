from langchain_core.prompts import PromptTemplate

from config import prompt_general
from graphs.states.research import ResearchState
from integrations.llm import llm_client


def call_llm_summarizer(structured_input: dict) -> str:
    prompt_template = PromptTemplate(
        template=prompt_general["final_summarizer"],
        input_variables=["structured_input"],
    )
    result = llm_client.completion(
        user_input=prompt_template.format(
            structured_input=structured_input,
        )
    )

    return result.strip()


def summarize(state: ResearchState) -> dict:
    if state.get("summarized"):
        return {}
    structured = state.get("structured_input")
    if not structured:
        return {}

    return {"summary": call_llm_summarizer(structured), "summarized": True}
