from langsmith import traceable

from graphs.states.research import ResearchState


@traceable
def validate_sources(state: ResearchState) -> dict:
    if state.get("validated"):
        return {}

    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")
    search_text = {
        k: v
        for k, v in {
            "search_general": state.get("search_general"),
            "search_founder": state.get("search_founder"),
            "search_finance": state.get("search_finance"),
            "search_news": state.get("search_news"),
        }.items()
        if v is not None
    }

    print("___")
    print(website_text)
    print("___")
    print(linkedin_text)
    print("___")
    print(search_text)

    return {
        "website_valid": bool(website_text and len(website_text) > 300),
        # # "search_valid": bool(search_text and len(search_text) > 50),
        # "search_valid": bool(search_text and len(search_text) > 0),
        "linkedin_valid": bool(linkedin_text and len(linkedin_text) > 100),
        "validated": True,
    }


def select_primary_and_secondary(state: ResearchState) -> dict:
    if state.get("sources_selected"):
        return {}

    sources = [
        ("website", state.get("website_text"), state.get("website_valid", False)),
        ("search", state.get("search_text"), state.get("search_valid", False)),
        ("linkedin", state.get("linkedin_text"), state.get("linkedin_valid", False)),
        # ("news", state.get("news_text"), state.get("news_valid", False)),
    ]

    # Keep only valid sources, in priority order
    valid_sources = [
        (name, text) for name, text, is_valid in sources if is_valid and text
    ]

    if not valid_sources:
        return {
            "primary_source": {},
            "secondary_sources": {},
        }

    primary_name, primary_text = valid_sources[0]

    secondary_sources = {name: text for name, text in valid_sources[1:]}

    return {
        "primary_source": {
            "source": primary_name,
            "text": primary_text,
        },
        "secondary_sources": secondary_sources,
        "sources_selected": True,
    }


@traceable
def select_and_validate(state: ResearchState) -> dict:
    # -----------------------------
    # Raw inputs
    # -----------------------------
    website_text = state.get("website_text")
    linkedin_text = state.get("linkedin_text")

    search_text = {
        k: v
        for k, v in {
            "general": state.get("search_general"),
            "founder": state.get("search_founder"),
            "finance": state.get("search_finance"),
            "news": state.get("search_news"),
        }.items()
        if v is not None
    }

    # -----------------------------
    # Validation rules
    # -----------------------------
    website_valid = bool(website_text and len(website_text) > 300)
    linkedin_valid = bool(linkedin_text and len(linkedin_text) > 100)
    search_valid = bool(search_text)

    # -----------------------------
    # Primary source selection
    # Priority: website > linkedin > search
    # -----------------------------
    primary_source = {}
    primary_type = None

    if website_valid:
        primary_source = website_text
        primary_type = "website"
    elif linkedin_valid:
        primary_source = linkedin_text
        primary_type = "linkedin"
    elif search_valid:
        # pick the most general search result first
        primary_source = search_text.get("general") or next(iter(search_text.values()))
        primary_type = "search"

    # -----------------------------
    # Secondary sources
    # -----------------------------
    secondary_sources = {}

    if website_valid and primary_type != "website":
        secondary_sources["website"] = website_text

    if linkedin_valid and primary_type != "linkedin":
        secondary_sources["linkedin"] = linkedin_text

    if search_valid and primary_type != "search":
        secondary_sources["search"] = search_text

    # -----------------------------
    # Single, safe state update
    # -----------------------------
    return {
        "website_valid": website_valid,
        "linkedin_valid": linkedin_valid,
        "search_valid": search_valid,
        "primary_source": {
            "source": primary_type,
            "text": primary_source,
        },
        "secondary_sources": secondary_sources,
    }


from graphs.nodes.judge import missing_fields, call_llm_judge
from graphs.nodes.summarizer import call_llm_summarizer


from typing import Dict, Optional


def build_structured_from_sources(
    primary_source: Optional[dict],
    secondary_sources: Dict[str, str],
    judge_output: Optional[dict],
) -> dict:

    structured = {
        "overview": "Not publicly available",
        "industry": "Not publicly available",
        "products_services": "Not publicly available",
        "target_customers": "Not publicly available",
        "value_proposition": "Not publicly available",
        "business_model": "Not publicly available",
        "use_cases": "Not publicly available",
        "sources_used": [],
    }

    # -------------------------
    # 1. Use primary source as baseline
    # -------------------------
    if primary_source and isinstance(primary_source, dict):
        primary_text = primary_source.get("text")
        primary_name = primary_source.get("source")

        if isinstance(primary_text, str) and primary_text.strip():
            structured["overview"] = primary_text
            structured["sources_used"].append(primary_name)

    # -------------------------
    # 2. Apply judge enrichment (authoritative overrides)
    # -------------------------
    if judge_output and isinstance(judge_output, dict):
        field_enrichment = judge_output.get("field_enrichment", {})

        if isinstance(field_enrichment, dict):
            for field, rule in field_enrichment.items():
                if not isinstance(rule, dict):
                    continue

                if not rule.get("use_secondary"):
                    continue

                source_key = rule.get("source")
                if not source_key:
                    continue

                text = secondary_sources.get(source_key)
                if isinstance(text, str) and text.strip():
                    structured[field] = text
                    structured["sources_used"].append(source_key)

    # -------------------------
    # 3. Fallback fill from secondary sources
    # -------------------------
    for field, value in structured.items():
        if value != "Not publicly available":
            continue

        for source_name, text in secondary_sources.items():
            if isinstance(text, str) and text.strip():
                structured[field] = text
                structured["sources_used"].append(source_name)
                break

    # -------------------------
    # 4. Deduplicate sources
    # -------------------------
    structured["sources_used"] = list(dict.fromkeys(structured["sources_used"]))

    return structured


def reason_and_summarize(state: ResearchState) -> dict:
    """
    Terminal reasoning node.
    Runs exactly once AFTER aggregate_inputs emits.
    """

    aggregated = state.get("aggregated_inputs")

    # 🔒 Guard: not ready yet
    if not aggregated:
        return {}

    print("RUNNING RR")
    print(aggregated)

    # Real logic would go here
    # return {"summary": "RUNNING RR"}
    # 1. Validate
    website_valid = bool(state.get("website_text") and len(state["website_text"]) > 300)
    linkedin_valid = bool(state.get("linkedin_text") and len(state["linkedin_text"]) > 100)
    search_valid = any(
        state.get(k)
        for k in (
            "search_general",
            "search_founder",
            "search_finance",
            "search_news",
        )
    )

    # 2. Select primary & secondary
    sources = []
    if website_valid:
        sources.append(("website", state["website_text"]))
    if search_valid:
        sources.append(("search", state.get("search_general")))
    if linkedin_valid:
        sources.append(("linkedin", state["linkedin_text"]))

    if not sources:
        primary_source = None
        secondary_sources = {}
    else:
        primary_name, primary_text = sources[0]
        primary_source = {"source": primary_name, "text": primary_text}
        secondary_sources = {n: t for n, t in sources[1:]}

    # 3. Judge if needed
    judge_output = None
    if primary_source and secondary_sources:
        missing = missing_fields(primary_source["text"])
        if missing:
            judge_output = call_llm_judge(
                primary=primary_source["text"],
                secondary=secondary_sources,
            )

    # 4. Build structured input
    structured_input = build_structured_from_sources(
        primary_source,
        secondary_sources,
        judge_output,
    )

    # 5. Summarize
    summary = call_llm_summarizer(structured_input)

    return {
        "primary_source": primary_source,
        "secondary_sources": secondary_sources,
        "judge_output": judge_output,
        "structured_input": structured_input,
        "summary": summary
    }



# def aggregate_inputs(state: ResearchState) -> dict:
#     """
#     Aggregate raw fetch/search outputs into a single, stable state.

#     This node should:
#     - Have multiple upstream edges
#     - Write exactly once
#     - Contain ZERO business logic
#     """

#     return {
#         # Raw sources
#         "website_text": state.get("website_text"),
#         "linkedin_text": state.get("linkedin_text"),

#         # Search outputs (already merged upstream if using search_all)
#         "search_general": state.get("search_general"),
#         "search_founder": state.get("search_founder"),
#         "search_finance": state.get("search_finance"),
#         "search_news": state.get("search_news"),
#     }

def aggregate_inputs(state: ResearchState) -> dict:
    """
    HARD BARRIER.
    Only emits once ALL inputs are present.
    """

    required = [
        state.get("website_text"),
        state.get("linkedin_text"),
        state.get("search_general"),
        state.get("search_founder"),
        state.get("search_finance"),
        state.get("search_news"),
    ]

    # 🔒 Barrier: do NOTHING until everything exists
    if not all(required):
        return {}

    # 🔒 Barrier: already aggregated
    if state.get("aggregated_inputs"):
        return {}

    return {
        "aggregated_inputs": {
            "website_text": state["website_text"],
            "linkedin_text": state["linkedin_text"],
            "search_general": state["search_general"],
            "search_founder": state["search_founder"],
            "search_finance": state["search_finance"],
            "search_news": state["search_news"],
        }
    }
