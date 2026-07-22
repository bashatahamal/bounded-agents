# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Detailed rationale for each change lives in [`docs/PROGRESS.md`](docs/PROGRESS.md).

## [0.3.1] — 2026-07-22

### Added
- `OpenAIProvider` accepts an optional `base_url`, so it works against any
  OpenAI-compatible endpoint (OpenRouter, Groq, local vLLM, ...), not just
  OpenAI itself. Added while wiring a consumer through OpenRouter's free
  tier. Two new tests (`tests/unit/test_openai_provider.py`).

## [0.3.0] — 2026-07-22

### Added
- `bounded.agent` — `Agent`, `Thread`, `ToolCall`, `ScopeError`: an
  LLM-driven tool-calling loop, the third layer (Tool / Workflow / **Agent**)
  the kit was missing. Bounded by a hard step limit, an optional code-level
  scope guard, and every failure captured as a `ToolCall.error` instead of
  crashing.
- `bounded.context` — `ContextSource` + `build_context_pack()`, a
  priority-ordered context-preface builder.
- `bounded.memory` — `Provenance`-ranked durable memory (`JsonlMemoryStore`)
  and `distill()` for extracting rules from feedback text.
- `bounded.json_repair` — the JSON-cleanup helpers factored out of
  `bounded.judge` once `bounded.memory` needed the identical logic.
- `bounded.adapters.agent.as_openai_tool()` and a `ToolCallingLLM` protocol
  + `OpenAIProvider.chat()`, the fourth Capability surface alongside
  CLI/LangGraph/MCP.
- `examples/task_assistant/` — a CLI chat agent (`uv run task-assistant`)
  proving the above end to end: four tools, a JSON-file task store, and a
  memory store whose contents actually show up in the next process's
  system prompt.
- 38 new tests (100 total, was 62).

### Known gaps
- The Agent layer is unverified against a real LLM in this environment (no
  API key available when it was built) — mocked tests only. See
  `docs/PROGRESS.md`'s Stage 5 entry.

## [0.2.0] — 2026-07-22

### Added
- `src/bounded/` — a reusable capability kit extracted from the original
  pipeline: `Capability[TIn, TOut]` primitive, registry, CLI/LangGraph/MCP
  adapters, generalized source arbitration (`bounded.arbitration`) and
  bounded-judge JSON parsing (`bounded.judge`), pluggable sinks
  (`GoogleSheetsSink`, `CsvSink`, `JsonlSink`), an `LLMProvider` protocol,
  retry/backoff (`bounded.resilience`), and opt-in LangSmith tracing
  (`bounded.observability`).
- `examples/company_research/` — the original pipeline, rebuilt on the kit.
- Test suite: 62 tests across `tests/unit/` and `tests/integration/`.
- `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`,
  `SECURITY.md`, this changelog, an Apache-2.0 `LICENSE`.
- Multi-stage, non-root, `uv.lock`-reproducible `Dockerfile`.

### Fixed
- `searchapp --help` used to crash with a raw pydantic `ValidationError`
  traceback if API keys weren't set — settings and API clients were built at
  import time. Now built lazily, on first actual use.
- `crawl_official_website` could raise `TypeError` on a page that failed to
  extract (`len(None)`), silently swallowed by a broad `except`. Fixed the
  underlying `None` check instead of relying on the catch-all.

### Changed
- Renamed project `search-to-sheets` → `bounded-agents`; Python package
  `bounded`.
- Package layout: flat `src/{config,graphs,helpers,integrations,services}`
  replaced by `src/bounded/` (the kit) + `examples/company_research/` (the
  example). Old layout deleted, not shimmed.

## [0.1.1] and earlier

Pre-restructure history: a working LangGraph pipeline (parallel source
fetch → deterministic arbitration → bounded LLM judge → summarize → Google
Sheets), no license, no tests, no CI. See `git log` for that era's commits.
