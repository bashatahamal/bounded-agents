## Overview

This document explains the **design thinking and development approach** behind **search-to-sheets**.

This document reflects **how the system was reasoned about**, including trade-offs, constraints, and explicit boundaries around LLM usage.

The system is designed to explore how public company information can be gathered, structured, and summarized in a way that is:

* Deterministic where possible
* Observable and debuggable during development
* Explicit about uncertainty and data gaps
* Continuity for further development
---

## Core Design Principles

1. **Determinism over autonomy**
   Control flow, source priority, and fallback behavior are enforced in code.

2. **Explicit uncertainty**
   Missing or conflicting information is surfaced explicitly rather than smoothed over.

3. **Bounded LLM usage**
   LLMs are used only where they add value (language synthesis and bounded analysis), never for authority or control decisions.

4. **Production-safe data acquisition**
   All data sources and collection methods are chosen to be legally safe, explainable, and robust.

---

## Workflow Orchestration (LangGraph)

LangGraph is used as a **procedural workflow framework** to make each step in the research pipeline explicit and traceable.

The intent is not to build an autonomous or self-directing agent, but rather:

* A stateful pipeline with clear stages
* Explicit inputs and outputs per step
* Deterministic transitions defined in code

Each node represents a concrete operation (e.g. fetch, validate, select, summarize), which makes it easier to inspect intermediate state during development.

> LangGraph is used as a deterministic workflow engine, not as an autonomous agent framework.

### Graph Visualization

During development, the LangGraph structure is visualized to understand:

* Execution order
* Conditional branches (e.g. whether a judge step is invoked)
* Data flow between nodes

*(Insert LangGraph Studio graph visualization here)*

---

## Source Acquisition Strategy

Public company data is gathered from multiple sources with explicit priority rules.

| Priority | Source                     | Rationale                       |
| -------: | -------------------------- | ------------------------------- |
|        1 | Official Website           | Most authoritative, first-party |
|        2 | LinkedIn (search snippets) | Structured business context     |
|        3 | Wikipedia / Crunchbase     | Secondary validation            |
|        4 | Search (Tavily / Serper)   | Coverage fallback               |

### Official Website

* Targeted crawl of explicitly defined pages (e.g. `/about`, `/products`)
* Boilerplate stripping and length validation
* Sitemap-guided crawling only when necessary and strictly capped

Official websites are treated as the **highest-confidence source** whenever available.

### LinkedIn Handling

To avoid ToS risks and brittle behavior:

* No HTML scraping
* No login-based access
* No browser automation

LinkedIn data is obtained only via **search-engine snippets**:

> LinkedIn data is obtained via search-engine snippets to avoid direct scraping and ensure compliance.

### Search Fallback

Search (Tavily / Serper) is used as a robust fallback, including domain-filtered queries (`site:company.com`) when direct crawling is unreliable or blocked.

---

## LLM Role (Strictly Bounded)

The LLM is used **only for summarization and synthesis**.

> The LLM does not browse, infer missing facts, or make assumptions.

All authority, prioritization, and fallback logic is enforced in code.

---

## Parallel Fetching vs. Source Arbitration

All sources are fetched in parallel to maximize coverage and latency efficiency. However, sources are **not treated equally**.

* Parallelism solves speed and availability
* Deterministic arbitration solves correctness and debuggability

> All sources are fetched in parallel to maximize coverage; source prioritization is applied only during synthesis to ensure authoritative data dominates the final summary.

---

## Deterministic Source Selection

The system selects:

* One primary authoritative source
* Optional secondary sources for controlled enrichment

Priority order:

1. Website
2. LinkedIn snippet
3. Search summary

This ensures predictable behavior, clear traceability, and prevents silent blending of conflicting claims.

---

## Bounded Judge Node (Optional)

A bounded LLM judge node is **optionally invoked** only when:

* A primary source exists
* Secondary sources are available
* The primary source is incomplete or vague

The judge:

* Identifies missing fields
* Flags bias or vagueness
* Recommends controlled enrichment

The judge **cannot**:

* Introduce new sources
* Override authority rules
* Merge conflicting facts
* Invent information

If the judge fails or returns incomplete output, the system falls back to deterministic priority-based merging.

> Authority remains in code; language synthesis is delegated to the LLM.

---

## Hybrid Merge Strategy

Rather than trusting the LLM entirely or enforcing rigid single-source rules, the system uses a hybrid approach:

* Code determines which sources may contribute
* The LLM determines how to phrase approved content

Secondary sources are included only when the primary source lacks coverage. Conflicts and uncertainty are surfaced explicitly.

---

## Failure Handling and Honesty

The system is designed so that:

* Partial data produces partial summaries
* Conflicts are acknowledged, not resolved implicitly
* Missing fields are stated explicitly
* Hallucination pressure is minimized

A weak public footprint is treated as a valid outcome, not a pipeline failure.

---

## Observability and Tracing (LangSmith)

LangSmith is used **during development** for observability rather than as a production dependency.

The primary goals are:

* Traceability of each LangGraph node execution
* Inspection of prompt and response pairs
* Monitoring token usage across steps
* Understanding how intermediate outputs influence final summaries

Specifically, LangSmith enables:

* Node-level traces for fetch, judge, and summarization steps
* Comparison of prompt iterations during development
* Debugging cases where outputs are incomplete, biased, or unexpected

This makes it possible to answer questions such as:

* Which source contributed to a specific part of the summary?
* Did the judge node run, and why?
* How much context and tokens were consumed per step?

### Trace and Output Inspection

LangSmith traces are used to:

* Re-run historical executions
* Inspect intermediate artifacts (validated sources, structured input)
* Correlate output quality with prompt or data changes

*(Insert LangSmith trace view screenshots here)*

### Token and Cost Awareness

Token usage is monitored at the step level to:

* Understand relative cost of each stage
* Avoid unbounded context growth
* Inform future optimization decisions

No automatic optimization or enforcement is applied; this monitoring is intended purely for developer insight.

*(Insert token usage / run statistics screenshots here)*

---

## Notes on Scope

This design intentionally avoids:

* Claiming optimal summarization quality
* Fully autonomous decision-making
* Aggressive crawling or scraping strategies

The goal is to document a **controlled, inspectable development approach**, not to present a finished or exhaustive company intelligence system.
