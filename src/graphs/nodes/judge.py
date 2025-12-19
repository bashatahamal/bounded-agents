import json

from langchain_core.prompts import PromptTemplate

from config import prompt_general
from graphs.states.research import ResearchState
from integrations.llm import llm_client

# Required keys expected in a search result
FIELD_KEYWORDS = {
    "products_or_services": [
        "product",
        "service",
        "platform",
        "solution",
        "offering",
        "tool",
    ],
    "industry": ["industry", "sector", "market", "vertical", "domain"],
    "target_customers": [
        "customer",
        "client",
        "user",
        "buyer",
        "business",
        "enterprise",
        "company",
        "organization",
        "smb",
        "startup",
    ],
    "value_proposition": [
        "value",
        "benefit",
        "advantage",
        "solve",
        "address",
        "problem",
        "pain point",
        "differentiation",
    ],
    "business_model": [
        "business model",
        "subscription",
        "pricing",
        "revenue",
        "monetization",
        "license",
        "fee",
    ],
    "use_cases": ["use case", "workflow", "application", "scenario", "example"],
    "technology_or_delivery": [
        "technology",
        "tech stack",
        "cloud",
        "ai",
        "ml",
        "api",
        "software",
        "saas",
        "infrastructure",
    ],
    "founders": ["founder", "co-founder", "founding team", "established by", "creator"],
    "finance": [
        "funding",
        "investment",
        "revenue",
        "profit",
        "valuation",
        "financial",
        "series a",
        "series b",
        "seed",
        "vc",
    ],
    "news": [
        "news",
        "announcement",
        "press release",
        "update",
        "launch",
        "partnership",
        "acquisition",
        "merger",
    ],
}


def build_structured_output(field_keywords: dict, state: dict | None = None) -> dict:
    structured = {
        "overview": (state.get("primary_source", {}).get("text") if state else None)
        or "Not publicly available"
    }

    for field in field_keywords.keys():
        structured[field] = "Not publicly available"

    return structured


def build_structured_input(state: ResearchState) -> ResearchState:
    structured = build_structured_output(FIELD_KEYWORDS, state)

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


def need_judge(state: ResearchState) -> bool:
    # The judge helps decide which secondary source can safely fill which missing field
    # if not state["primary_source"]:
    if not len(state["secondary_sources"]) > 0:
        return False

    missing = missing_fields(state["primary_source"].get("text"))
    print(f"Missing: {missing}")

    return len(missing) > 0 and len(state["secondary_sources"]) > 0


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
    try:
        return {
            "judge_output": call_llm_judge(
                primary=state["primary_source"].get("text"),
                secondary=state["secondary_sources"],
            )
        }
    except Exception as e:
        return {
            "judge_output": None,
            "errors": [f"Judge failed: {str(e)}"],
        }
