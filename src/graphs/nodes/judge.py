import json

from langchain_core.prompts import PromptTemplate

from config import prompt_general
from graphs.states.research import ResearchState
from integrations.llm import llm_client

# Required keys expected in a search result
# FIELD_KEYWORDS = {
#     "products_or_services": ["product", "service", "platform", "solution"],
#     "industry": ["industry", "sector", "market"],
#     "target_customers": ["customer", "client", "business", "enterprise", "SMB"],
# }
FIELD_KEYWORDS = {
    "products_or_services": ["product", "service", "platform", "solution"],
    "industry": ["industry", "sector", "market"],
    "target_customers": ["customer", "client", "business", "enterprise", "SMB"],
    "value_proposition": ["value", "benefit", "solve", "problem"],
    "business_model": ["subscription", "pricing", "revenue", "license"],
    "use_cases": ["use case", "workflow", "application"],
    "technology_or_delivery": ["cloud", "AI", "API", "software"],
}


def build_structured_input(state: ResearchState) -> ResearchState:
    structured = {
        "overview": state.get("primary_source").get("text") or "Not publicly available",
        "industry": "Not publicly available",
        "products_or_services": "Not publicly available",
        "target_customers": "Not publicly available",
        "value_proposition": "Not publicly available",
        "business_model": "Not publicly available",
        "use_cases": "Not publicly available",
        "technology_or_delivery": "Not publicly available",
    }

    judge = state.get("judge_output")

    # If judge is usable, enrich selectively
    if judge and "field_enrichment" in judge:
        for field, rule in judge["field_enrichment"].items():
            if rule.get("use_secondary"):
                src = rule.get("source")
                if src in state["secondary_sources"]:
                    structured[field] = state["secondary_sources"][src]

    # HARD FALLBACK — if judge missing or incomplete
    for field, value in structured.items():
        if value == "Not publicly available":
            for src in ["website_text", "linkedin_text", "search_text"]:
                if state.get(src):
                    structured[field] = state[src]
                    break

    state["structured_input"] = structured
    return state


def missing_fields(primary_text: str) -> list[str]:
    missing = []
    for field, keywords in FIELD_KEYWORDS.items():
        if not any(k.lower() in primary_text.lower() for k in keywords):
            missing.append(field)
    return missing


# def need_judge(state: ResearchState) -> bool:
#     # The judge helps decide which secondary source can safely fill which missing field
#     # if not state["primary_source"]:
#     if not len(state["secondary_sources"]) > 0:
#         return False

#     missing = missing_fields(state["primary_source"].get("text"))
#     print(f"Missing: {missing}")

#     return len(missing) > 0 and len(state["secondary_sources"]) > 0


def need_judge(state: ResearchState) -> bool:
    # ---- GUARD 1: already judged ----
    # Prevent judge from running more than once
    if state.get("judge_output") is not None:
        return False

    primary = state.get("primary_source")
    secondary = state.get("secondary_sources")

    # ---- GUARD 2: missing required inputs ----
    if not primary or not isinstance(primary, dict):
        return False

    primary_text = primary.get("text")
    if not primary_text or not isinstance(primary_text, str):
        return False

    if not secondary or not isinstance(secondary, dict):
        return False

    if len(secondary) == 0:
        return False

    # ---- CORE LOGIC ----
    missing = missing_fields(primary_text)

    # Optional debug (safe)
    if missing:
        print(f"Missing fields → triggering judge: {missing}")

    return len(missing) > 0


def call_llm_judge(primary: str, secondary: dict) -> dict:
    prompt_template = PromptTemplate(
        template=prompt_general["call_judge"],
        input_variables=["primary", "secondary", "required_fields"],
    )
    result = llm_client.completion(
        user_input=prompt_template.format(
            primary=primary,
            secondary=secondary,
            required_fields="\n".join(f"- {key}" for key in FIELD_KEYWORDS.keys()),
        )
    )

    # return result.strip()
    return json.loads(result)


def judge_node(state: ResearchState) -> dict:
    if state.get("judged"):
        return {}

    try:
        return {
            "judge_output": call_llm_judge(
                primary=state["primary_source"].get("text"),
                secondary=state["secondary_sources"],
            ),
            "judged": True,
        }
    except Exception as e:
        return {
            "judge_output": None,
            "errors": [f"Judge failed: {str(e)}"],
        }
