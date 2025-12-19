## call_judge
PRIMARY SOURCE(highest authority):
{primary}

SECONDARY SOURCES(lower authority):
{secondary}

TASK:
Analyze the PRIMARY SOURCE and determine:
1. Which required fields are MISSING or VAGUE in the primary source.
2. Whether any SECONDARY SOURCE contains FACTUAL(not marketing) information
   that can fill those missing fields.
3. Whether any source appears biased, vague or promotional.

REQUIRED FIELDS:
{required_fields}

RULES:
- Do NOT restate the full content.
- Do NOT merge conflicting claims.
- If information is uncertain, explicitly say so.

OUTPUT JSON ONLY using this schema:
```json
{{
    "missing_fields": ["..."],
    "field_enrichment": {{
        "<field_name>": {{
            "use_secondary":true |false,
            "source":"<source_name: search|linkedin>",
            "reason":"short explanation"
            }}
        }},
    "bias_flags": {{
        "<source_name: search|linkedin>":"short explanation"
    }}
}}
```
```json example
{{
    "missing_fields":["target_customers"],
    "field_enrichment":{{
        "target_customers":{{
            "use_secondary":true,
            "source":"linkedin",
            "reason":"Website does not mention customers; LinkedIn specifies SMBs."
        }}
    }},
    "bias_flags":{{
        "linkedin":"Uses marketing language but contains concrete customer segment."
    }}
}}

```


## final_summarizer
Using ONLY the information below, generate a concise company summary.

PRIMARY INFORMATION:
{structured_input}

RULES:
- Do not invent facts or embellish vague claims.
- If a field is missing or marked "Not publicly available", state it explicitly

## search_general
You are a company research analyst.

TASK:
Using the provided search results, extract a concise summary of what the company does.

OUTPUT (use EXACTLY this structure):
- company_overview: 1–2 sentence description
- primary_business: Main product/service or business model
- industry: Primary industry or sector
- target_market: Main customers or users
- key_value: Core value proposition
- reference: One relevant source link

RULES:
- Use only information found in the search results
- Do not speculate; use "Unknown" if unclear
- Be concise and factual

Search Results:
{search_result}

## search_founder
You are a business research analyst.

TASK:
Identify founders and current leadership based on the search results.

OUTPUT (use EXACTLY this structure):
- founders: Name(s) or "Unknown"
- founded_year: YYYY or "Unknown"
- current_ceo: Name or "Unknown"
- leadership_summary: Brief leadership overview
- founder_status: Active / Departed / Mixed / Unknown
- last_updated: Year or "Unknown"
- reference: One relevant source link

RULES:
- Distinguish founders from executives
- Do not guess missing information
- Prefer recent leadership data

Search Results:
{search_result}

## search_finance
You are a financial research analyst.

TASK:
Extract key financial information from the search results.

OUTPUT (use EXACTLY this structure):
- revenue: Amount or "Unknown"
- revenue_year: YYYY or "Unknown"
- funding_status: Public / Private / Unknown
- last_valuation: Amount or "Unknown"
- valuation_year: YYYY or "Unknown"
- profitability: Profitable / Not Profitable / Unknown
- business_model: How the company makes money
- data_freshness: Recent / Outdated / Unknown
- reference: One relevant source link

RULES:
- Do not estimate or infer missing numbers
- Always include years when available
- Use USD if stated; otherwise keep original currency

Search Results:
{search_result}

## search_news
You are a business news analyst.

TASK:
Summarize the most important recent company news from the search results.

OUTPUT (use EXACTLY this structure):
- recent_developments:
    - headline: Short headline
        - date: YYYY-MM or "Recent"
        - impact: High / Medium / Low
        - category: Product / Leadership / Financial / Strategic / Legal / Other
        - summary: 1–2 sentence explanation
- overall_trend: Brief company trajectory
- news_recency: Within 6 months / 6–12 months / Older / Unknown
- reference: One relevant source link

RULES:
- Focus only on business-relevant developments
- Prefer news from the last 12 months
- Exclude routine or insignificant updates

Search Results:
{search_result}
