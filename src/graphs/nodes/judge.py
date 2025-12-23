import json

from langchain_core.prompts import PromptTemplate

from config import prompt_general
from graphs.states.research import ResearchState
from helpers.json_validators import (
    FIELD_KEYWORDS,
    _extract_json_object,
    _normalize_quotes,
    _remove_trailing_commas,
    _strip_markdown_fences,
    _validate_schema,
)
from integrations.llm import llm_client


def build_structured_output(field_keywords: dict, state: dict | None = None) -> dict:
    structured = {
        "overview": (state.get("primary_source", {}).get("text") if state else None)
        or "Not publicly available"
    }

    for field in field_keywords.keys():
        structured[field] = "Not publicly available"

    return structured


def collect_gathered_knowledge(state: ResearchState) -> dict:
    return {
        "primary": {
            k: v
            for k, v in state.items()
            if k.endswith("_text") or k.startswith("search_")
        },
        "secondary": state.get("secondary_sources", {}),
    }


def build_structured_input(state: ResearchState) -> ResearchState:
    structured = {
        "gathered_knowledge": collect_gathered_knowledge(state),
        "fields": {field: "Not publicly available" for field in FIELD_KEYWORDS.keys()},
    }

    judge = state.get("judge_output")

    # ---------------------------------------
    # NO JUDGE → ignore fields entirely
    # ---------------------------------------
    if not judge:
        state["structured_input"] = structured
        return state

    # ---------------------------------------
    # JUDGE PRESENT → populate via judge only
    # ---------------------------------------
    secondary_sources = state.get("secondary_sources", {})
    used_secondary_keys: set[str] = set()

    if isinstance(judge, dict) and isinstance(judge.get("field_enrichment"), dict):
        for field, rule in judge["field_enrichment"].items():
            if field not in structured["fields"]:
                continue
            if not isinstance(rule, dict):
                continue

            if rule.get("use_secondary") is True:
                src = rule.get("source")
                if src in secondary_sources:
                    structured["fields"][field] = secondary_sources[src]
                    used_secondary_keys.add(src)

    # ---------------------------------------
    # REMOVE consumed secondary knowledge
    # ---------------------------------------
    if used_secondary_keys:
        structured["gathered_knowledge"]["secondary"] = {
            k: v
            for k, v in structured["gathered_knowledge"]["secondary"].items()
            if k not in used_secondary_keys
        }

    state["structured_input"] = structured
    return state


def need_judge(state: ResearchState) -> bool:
    return not state["valid_summary"]


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

    raw = result.strip()

    # ---------------------------------------
    # Defensive cleanup pipeline
    # ---------------------------------------
    raw = _strip_markdown_fences(raw)
    raw = _normalize_quotes(raw)
    raw = _remove_trailing_commas(raw)

    json_text = _extract_json_object(raw)
    if not json_text:
        return {
            "error": "No JSON object found",
            "raw": result,
        }

    try:
        parsed = json.loads(json_text, strict=False)
    except json.JSONDecodeError as e:
        return {
            "error": "JSON parsing failed",
            "reason": str(e),
            "raw": json_text,
        }

    # ---------------------------------------
    # Schema & safety validation
    # ---------------------------------------
    if not isinstance(parsed, dict):
        return {
            "error": "Judge output is not a JSON object",
            "raw": parsed,
        }

    validated = _validate_schema(parsed)

    return validated


def judge_node(state: ResearchState) -> dict:
    try:
        if state.get("judged", False):
            return {
                "valid_summary": True,
                "judged": True,
            }

        return {
            "judge_output": call_llm_judge(
                primary=state["primary_source"].get("text"),
                secondary=state["secondary_sources"],
            ),
            "valid_summary": True,
            "judged": True,
        }
    except Exception as e:
        return {
            "judge_output": None,
            "errors": [f"Judge failed: {str(e)}"],
            "valid_summary": True,
        }


# def build_structured_input(state: ResearchState) -> ResearchState:
#     structured = build_structured_output(FIELD_KEYWORDS, state)

#     judge = state.get("judge_output")

#     # If judge is usable, enrich selectively
#     if judge and "field_enrichment" in judge:
#         for field, rule in judge["field_enrichment"].items():
#             if rule.get("use_secondary"):
#                 src = rule.get("source")
#                 if src in state["secondary_sources"]:
#                     structured[field] = state["secondary_sources"][src]

#     # HARD FALLBACK — if judge missing or incomplete
#     for field, value in structured.items():
#         if value == "Not publicly available":
#             for src in [
#                 "website_text",
#                 "linkedin_text",
#                 "search_general",
#                 "search_founder",
#                 "search_finance",
#                 "search_news",
#             ]:
#                 if state.get(src):
#                     structured[field] = state[src]
#                     break

#     state["structured_input"] = structured
#     return state


# def missing_fields(primary_text: str) -> list[str]:
#     missing = []
#     for field, keywords in FIELD_KEYWORDS.items():
#         if not any(k.lower() in primary_text.lower() for k in keywords):
#             missing.append(field)
#     return missing


# def need_judge(state: ResearchState) -> bool:
#     # The judge helps decide which secondary source can safely fill which missing field
#     # if not state["primary_source"]:
#     if not len(state["secondary_sources"]) > 0:
#         state["valid_summary"] = True
#         return False

#     missing = missing_fields(state["primary_source"].get("text"))
#     print(f"Missing: {missing}")

#     state["valid_summary"] = False
#     return len(missing) > 0 and len(state["secondary_sources"]) > 0


# def call_llm_judge(primary: str, secondary: dict) -> dict:
#     prompt_template = PromptTemplate(
#         template=prompt_general["call_judge"],
#         input_variables=["primary", "secondary", "required_fields"],
#     )
#     result = llm_client.completion(
#         user_input=prompt_template.format(
#             primary=primary,
#             secondary=secondary,
#             required_fields="\n".join(f"- {key}" for key in FIELD_KEYWORDS.keys()),
#         )
#     )

#     # return result.strip()
#     # print("Raw LLM result:", repr(result))

#     try:
#         return json.loads(result)
#     except json.JSONDecodeError:
#         # Try to salvage JSON substring
#         start = result.find("{")
#         end = result.rfind("}") + 1
#         if start != -1 and end != -1:
#             return json.loads(result[start:end])
#         else:
#             return {"error": "Invalid JSON", "raw": result}
