from __future__ import annotations

from langchain_core.prompts import PromptTemplate

from bounded.judge import run_bounded_judge
from company_research.fields import FIELD_KEYWORDS
from company_research.llm_client import get_llm_client
from company_research.prompts import get_prompts
from company_research.state import ResearchState


def need_judge(state: ResearchState) -> bool:
    return not state["valid_summary"]


def judge_node(state: ResearchState) -> dict:
    if state.get("judged", False):
        return {"valid_summary": True, "judged": True}

    try:
        template = PromptTemplate(
            template=get_prompts()["call_judge"],
            input_variables=["primary", "secondary", "required_fields"],
        )
        prompt = template.format(
            primary=(state.get("primary_source") or {}).get("text"),
            secondary=state.get("secondary_sources") or {},
            required_fields="\n".join(f"- {key}" for key in FIELD_KEYWORDS),
        )
        output = run_bounded_judge(
            llm=get_llm_client(), prompt=prompt, allowed_fields=set(FIELD_KEYWORDS)
        )
        judge_output = {
            "missing_fields": output.missing_fields,
            "field_enrichment": output.field_enrichment,
            "bias_flags": output.bias_flags,
        }
        return {"judge_output": judge_output, "valid_summary": True, "judged": True}
    except Exception as e:
        # If the judge fails or returns something unsalvageable, the pipeline
        # continues safely using the deterministic fallback (build_input runs
        # with judge_output=None, so structured_input falls back to
        # primary-source-only). Authority never depends on the judge working.
        return {"judge_output": None, "errors": [f"Judge failed: {e}"], "valid_summary": True}


def collect_gathered_knowledge(state: ResearchState) -> dict:
    return {
        "primary": {
            k: v for k, v in state.items() if k.endswith("_text") or k.startswith("search_")
        },
        "secondary": state.get("secondary_sources", {}),
    }


def build_structured_input(state: ResearchState) -> ResearchState:
    structured = {
        "gathered_knowledge": collect_gathered_knowledge(state),
        "fields": {field: "Not publicly available" for field in FIELD_KEYWORDS},
    }

    judge = state.get("judge_output")
    if not judge:
        state["structured_input"] = structured
        return state

    secondary_sources: dict = state.get("secondary_sources") or {}
    used_secondary_keys: set[str] = set()

    field_enrichment = judge.get("field_enrichment") if isinstance(judge, dict) else None
    if isinstance(field_enrichment, dict):
        for field, rule in field_enrichment.items():
            if field not in structured["fields"] or not isinstance(rule, dict):
                continue
            if rule.get("use_secondary") is True:
                src = rule.get("source")
                if isinstance(src, str) and src in secondary_sources:
                    structured["fields"][field] = secondary_sources[src]
                    used_secondary_keys.add(src)

    if used_secondary_keys:
        structured["gathered_knowledge"]["secondary"] = {
            k: v
            for k, v in structured["gathered_knowledge"]["secondary"].items()
            if k not in used_secondary_keys
        }

    state["structured_input"] = structured
    return state
