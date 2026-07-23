"""The company-research schema: field name -> keywords that count as coverage.

This is domain config, not framework code -- it's what `bounded.arbitration`
and `bounded.judge` are parameterized by for *this* example. A different
example (e.g. product research, incident triage) would define its own field
map and reuse the same kit.
"""

FIELD_KEYWORDS: dict[str, list[str]] = {
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
