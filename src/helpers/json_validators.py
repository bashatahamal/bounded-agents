import re

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

ALLOWED_FIELD_KEYS = set(FIELD_KEYWORDS.keys())
ALLOWED_TOP_LEVEL_KEYS = {
    "missing_fields",
    "field_enrichment",
    "bias_flags",
}


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _normalize_quotes(text: str) -> str:
    return text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")


def _remove_trailing_commas(text: str) -> str:
    # Removes trailing commas before } or ]
    return re.sub(r",\s*([}\]])", r"\1", text)


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _normalize_field_enrichment_keys(field_enrichment: dict) -> dict:
    """
    Fix common LLM errors like:
    ' founders', '" founders"', 'founders ', etc.
    """
    normalized = {}
    for raw_key, value in field_enrichment.items():
        clean_key = raw_key.strip().strip('"').strip()
        if clean_key in ALLOWED_FIELD_KEYS:
            normalized[clean_key] = value
    return normalized


def _validate_schema(data: dict) -> dict:
    """
    Enforce minimal schema correctness.
    Drop unknown keys instead of failing.
    """
    validated = {}

    for key in ALLOWED_TOP_LEVEL_KEYS:
        if key in data:
            validated[key] = data[key]

    # Ensure expected structures
    validated.setdefault("missing_fields", [])
    validated.setdefault("field_enrichment", {})
    validated.setdefault("bias_flags", {})

    # Normalize field_enrichment keys
    if isinstance(validated["field_enrichment"], dict):
        validated["field_enrichment"] = _normalize_field_enrichment_keys(
            validated["field_enrichment"]
        )
    else:
        validated["field_enrichment"] = {}

    return validated
