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
