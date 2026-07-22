# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Detailed rationale for each change lives in [`docs/PROGRESS.md`](docs/PROGRESS.md).

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
