# Progress Log

Live tracker for the `bounded-agents` rebuild. Repo started life as
`search-to-sheets`, a working take-home-style pipeline; this log tracks its
conversion into a reusable, public-facing "capability kit" with company
research as the reference example.

Update convention: newest entry on top. Each entry says what changed, why,
and what's still open.

---

## Plan (5 stages)

1. **Stage 0 — safe to publish.** License, strip anything pointing at the
   live demo spreadsheet / ex-employer, remove hardcoded IDs. *(repo was
   already public on GitHub — this stage is about hygiene, not visibility.)*
2. **Stage 1 — package + tooling.** Real `src/bounded/` namespace, lint/type
   config, pre-commit, CI, reproducible Docker build.
3. **Stage 2 — extract the kit.** `Capability[TIn, TOut]` primitive +
   registry + adapters (LangGraph node / CLI / MCP tool), arbitration and
   judge lifted out of the company-research domain into reusable pieces,
   pluggable sinks. Company research becomes `examples/company_research/`
   built on top of the kit.
4. **Stage 3 — tests + resilience.** Unit tests on the pure logic, fixture
   tests on fetchers, retry/backoff/timeouts, typed errors.
5. **Stage 4 — shop window.** README rewrite, CONTRIBUTING, SECURITY,
   CHANGELOG, issue/PR templates, Makefile.

Naming: package `bounded`, repo `bounded-agents` (renamed in place from
`search-to-sheets`, GitHub keeps the old URL as a redirect).

---

## Log

### Transition PR — done (2026-07-22)

Since the whole rebuild landed via direct pushes to `main` rather than a
branch + PR, there was no single reviewable artifact showing the "before"
and "after" together. Added one retroactively:

- Pushed a `legacy/search-to-sheets` branch pinned at `5219d27` — the last
  commit before Stage 0 touched anything.
- Opened [PR #1](https://github.com/bashatahamal/bounded-agents/pull/1)
  (base: `legacy/search-to-sheets`, head: `main`): the full 86-file diff,
  with a description that reuses the existing `assets/` screenshots
  (`main-graph.png`, `judge-node.png`, `selectsource.png`) to explain the
  "authority in code, phrasing in the LLM" idea, framed as an engineering
  decision — no mention of the circumstances that prompted the rebuild.
  The PR body says plainly that it mirrors what's already on `main` and
  exists for reviewability, not as pending work.
- Not merged (nothing to merge — `main` already has this state) and not
  intended to be; it's a standalone, permanently linkable artifact.

### Repo rename + push — done (2026-07-22)

- Renamed the GitHub repo `search-to-sheets` → `bounded-agents` via
  `gh repo rename` (GitHub keeps the old URL as a redirect). Updated the
  repo's description metadata to match (it's a separate field from
  `README.md` — easy to forget).
- **Push hit a snag**: the authenticated `gh`/git token (`bashatahamal`,
  the repo owner) has scopes `admin:public_key, gist, read:org, repo` —
  no `workflow` scope, so GitHub rejected any push touching
  `.github/workflows/ci.yml`. A second logged-in account
  (`bashatahamal-bais`) *does* have the `workflow` scope but only has
  read (`pull`) access to this repo, not push — so switching accounts
  wasn't a fix, just a dead end (checked via `gh api
  repos/.../permissions` before assuming otherwise).
- Asked how to handle it rather than guessing; the answer was to push
  everything except that one file now. Since none of the three staged
  commits (Stage 0 / Stages 1-3 / Stage 4) had been pushed yet — the
  earlier `git push` failed atomically, so nothing partial landed —
  reorganizing local-only history was safe: `git reset --soft` back to
  the original base, dropped `ci.yml` from the index, and re-committed
  everything as one squashed commit (fine to squash here specifically
  *because* it was still 100% unpublished; this is not the general
  practice for this repo going forward).
- Pushed `3550ff7` to `bashatahamal/bounded-agents`. Re-ran the full
  `make check` against that exact commit before pushing, not just
  before the squash.
- Committed `.github/workflows/ci.yml` again locally right after
  (`e2f66df`) — sitting on `main`, not pushed. Push it once the scope is
  refreshed:
  ```bash
  gh auth refresh -h github.com -s workflow
  git push origin main
  ```

**Status: done**, modulo that one follow-up push above.

### Stage 4 — done (2026-07-22)

- `README.md` rewritten from scratch: leads with the "authority in code,
  phrasing in the LLM" thesis, quickstart that works before any credentials
  exist, a table of every `bounded/` module and what it's for, the example's
  graph flow, a sinks-swap example (verified it actually runs, not just
  written), LangGraph Studio instructions, dev commands.
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` (Keep a Changelog format,
  0.2.0 entry covers this whole restructure).
- `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`.
- `Makefile` (`install`, `test`, `lint`, `format`, `typecheck`, `check`,
  `run`, `docker-build`, `docker-up`, `clean`) — ran `make check` for real,
  not just eyeballed: ruff, mypy, pytest (62 passed), ruff format --check
  all green.

**Next up:** rename the GitHub repo `search-to-sheets` → `bounded-agents`,
push, verify the redirect.

### Stage 1-3 — done (2026-07-22)

Did these three together in practice: the package restructure *was* the kit
extraction, and tests followed immediately behind each piece rather than as
a separate pass.

**Package layout**
- New `src/bounded/` — the reusable kit — and `examples/company_research/`
  — the flagship example, rebuilt on top of it. Old flat `src/{config.py,
  main.py, graphs/, helpers/, integrations/, services/, prompts/}` deleted
  outright (not deprecated/shimmed) once the replacement was verified
  working end-to-end.
- `pyproject.toml`: renamed to `bounded-agents`, `packages.find.where =
  ["src", "examples"]` so `company_research` installs as a top-level
  package alongside `bounded` without an awkward `examples.` import
  prefix. Added `langchain-core`, `langsmith`, `requests`, `tenacity`,
  `typing-extensions` as *direct* dependencies (previously relied on
  transitive resolution through `langgraph` — worked by luck, not by
  contract). Added `dev` extras (pytest, ruff, mypy) and their configs.

**The kit (`src/bounded/`)**
- `capability.py` — `Capability[TIn: BaseModel, TOut: BaseModel]` (PEP 695
  generics): one typed input model, one typed output model, one `run`
  callable. This is the "register once, run three ways" primitive.
- `registry.py` — trivial name -> Capability lookup.
- `adapters/langgraph.py` — `as_langgraph_node()` wraps a Capability as a
  dict-in/dict-out graph node; `safe_merge()` (moved here from the
  example, it was already fully generic) is the LangGraph state-merge
  reducer.
- `adapters/cli.py` — turns a Capability's pydantic input model into an
  argparse subcommand automatically (field -> flag, required-ness
  preserved).
- `adapters/mcp.py` — describes a Capability as an MCP tool dict (name,
  description, JSON schemas, handler) without taking a hard dependency on
  any specific MCP SDK.
- `arbitration.py` — `Source` / `select()`: the deterministic
  primary/secondary source selection that used to be
  `select_primary_and_secondary` in `validation.py`, generalized to take
  a `field_keywords` map instead of hardcoding the company-research
  schema. This is the actual load-bearing idea from `docs/DESIGN.md`
  ("authority in code").
- `judge.py` — `parse_judge_output()` / `run_bounded_judge()`: the
  defensive JSON-cleanup pipeline that used to be
  `helpers/json_validators.py`, generalized the same way. Raises
  `JudgeError` instead of returning a `{"error": ...}` sentinel dict —
  callers now `except JudgeError` instead of checking a magic key.
- `sinks/` — `Sink` protocol + `GoogleSheetsSink` (the old
  `GoogleSheetsClient`, moved and given a `write(columns, rows,
  destination=...)` method matching the protocol) + new `CsvSink` /
  `JsonlSink`. Proves the "Sheets is one sink, not the point" claim.
- `llm/` — `LLMProvider` protocol + `OpenAIProvider` (the old `LLMClient`,
  trimmed to what's actually used — dropped `completion_with_websearch`,
  `completion_async`, `_build_messages`, none of which were called
  anywhere or tested).
- `credentials.py` — `load_json_credentials()` replaces the 3-attempt
  recursive JSON-unmangling in the old `config.py`. Accepts a file path,
  base64, or raw JSON string; raises `ValueError` on anything else
  instead of ever silently returning `{}`.
- `resilience.py` — `with_retry()`, a thin `tenacity` wrapper (exponential
  backoff, narrowable `retry_on`). Applied to the Serper HTTP calls, page
  extraction, and the OpenAI provider's `complete()`.
- `observability.py` — `configure_logging()` (structlog setup, now called
  explicitly in `main()` instead of as an import-time side effect) and
  `maybe_wrap_openai()` (opt-in LangSmith tracing, only if
  `LANGSMITH_API_KEY`/`LANGCHAIN_API_KEY` is set and `langsmith` is
  importable — tracing was already optional per the README, now the code
  actually reflects that instead of importing `wrap_openai`
  unconditionally).
- `prompts.py` — `load_markdown_sections()`, the old
  `helpers/read_markdown.py` unchanged in behavior, moved because it's
  generic (any `## heading`-delimited markdown file).

**The example (`examples/company_research/`)**
- Same graph shape, same node behavior, same prompts — this was a port,
  not a rewrite of the pipeline logic. `fields.py` holds the
  company-research-specific `FIELD_KEYWORDS` schema (now explicitly
  "domain config, not framework code" per its own docstring).
- **Fixed a real bug carried over from the original**: `crawl_official_website`
  did `if len(text) > 200` without checking `text is not None` first —
  `extract_text_from_url` can return `None`, which would have raised
  `TypeError` inside the per-path `except Exception: continue`, silently
  swallowed. Now `if text and len(text) > 200`.
- **Fixed eager settings/client instantiation**, the thing flagged during
  the initial repo review: `Settings()` was built at module import time in
  the old `config.py`, and the Tavily client / `LLMClient()` singleton were
  also built at import time in their respective modules. That meant
  `uv run searchapp --help` used to crash with a raw pydantic
  `ValidationError` traceback before argparse ever got to print help —
  confirmed this failure mode before touching anything (see below), then
  fixed it by making `get_settings()`, `get_llm_client()`, and
  `_tavily_client()` all `functools.lru_cache`'d functions called lazily
  from inside node functions, never at import time. `--help` now works
  with zero environment variables set.
- `state.py`: `ResearchState` fields other than `company_name` are now
  `NotRequired` — accurate to how the graph is actually invoked (`{"company_name":
  ...}`), and is what got mypy to a clean pass on `graph.invoke(...)` instead of
  quieting it with an ignore comment. Also dropped `aggregated_inputs: dict |
  None`, a state field that was declared but never read or written anywhere.

**Verification** (all run in this session, not assumed):
- `uv run searchapp --help` with `OPENAI_API_KEY` / `TAVILY_API_KEY` /
  `SERPER_API_KEY` / `GOOGLE_SHEET_ACCESS_CREDS` all unset -> works,
  confirmed broken before the settings-laziness fix.
- `company_research.graph` builds with zero credentials present.
- Full `graph.invoke({"company_name": ...})` run with fetchers and the LLM
  client mocked: website selected as primary source, judge failure (mocked
  non-JSON LLM output) handled exactly per the documented fallback —
  `valid_summary` stays `True`, a real summary still comes out the other
  end. This is the deterministic-fallback claim from `docs/DESIGN.md`
  actually exercised, not just asserted.
- `uv run ruff check` / `uv run ruff format --check` / `uv run mypy src
  examples` / `uv run pytest -q` — all clean. 62 tests (arbitration, judge
  parsing, credentials, resilience/retry, CLI + MCP + LangGraph adapters,
  registry, prompt-file loader, sinks, observability's LangSmith opt-in,
  the company-research validate/arbitration integration, and fixture-based
  fetcher tests mocking `requests`).
- Coverage is uneven by design, not oversight: `bounded`'s pure logic
  (arbitration, judge, adapters, credentials, resilience, csv/jsonl sinks)
  is at or near 100%. Thin glue that's mostly third-party calls
  (`graph.py` wiring, `service.py`, `main.py`, `sheets.py`,
  `openai_provider.py`'s actual API call) is exercised by the mocked
  end-to-end run above but not unit-tested line-by-line — testing those
  further would mostly be re-testing gspread/OpenAI's own clients.

**Tooling added**
- `.pre-commit-config.yaml` (ruff check --fix, ruff format, end-of-file /
  trailing-whitespace / merge-conflict / large-file hooks).
- `.github/workflows/ci.yml` — ruff check, ruff format --check, mypy,
  pytest, on Python 3.12 and 3.13.
- `Dockerfile` rewritten multi-stage (uv-based, dependency layer cached
  separately from source, `--frozen` against `uv.lock` so the image is
  reproducible instead of drifting via `pip install .`), runs as a
  non-root `app` user. **Not verified in this session** — Docker Desktop
  isn't running in this environment and I didn't force it up; the
  Dockerfile follows uv's documented multi-stage pattern but `docker
  build` itself hasn't actually been run. Flagging this explicitly rather
  than claiming it works.
- `docker-compose.yml` updated to match (service renamed, mounts both
  `src/` and `examples/` for hot-reload, dropped the `PYTHONPATH` hack
  since the editable install resolves packages correctly on its own).

**Next up: Stage 4** — README rewrite, CONTRIBUTING, SECURITY, CHANGELOG,
issue/PR templates, Makefile. Then the GitHub repo rename.

### Stage 0 — done (2026-07-22)
- Added `docs/PROGRESS.md` (this file).
- Added `LICENSE` (Apache-2.0).
- `.gitignore`: excluded `.claude/settings.local.json` (local tool-permission
  grants, never shared).
- `docs/DESIGN.md`: removed the live demo spreadsheet link and both
  LangSmith public-trace links — the screenshots already in `assets/`
  carry the same evidence without pointing at a live, personally-linked
  resource.
- Removed hardcoded spreadsheet ID from the `__main__` blocks in
  `src/integrations/sheet.py` and `src/services/company_research.py`
  (dead debug entry points, not part of the public CLI surface).
- Removed a broken `__main__` block in `src/integrations/llm.py` (called
  `llm_client.generate(...)`, a method that doesn't exist — dead and
  would error if anyone ran the file directly).
- Deleted ~140 lines of commented-out dead code: an old `select_and_validate`
  implementation superseded by `select_primary_and_secondary`
  (`src/graphs/nodes/validation.py`), and an unused `build_structured_output`
  plus a fully-commented legacy version of `build_structured_input` /
  `need_judge` / `call_llm_judge` (`src/graphs/nodes/judge.py`).
- Set repo-local git identity (`bashatahamal@gmail.com`) so new commits
  don't carry a work email domain — old commits (including one under an
  earlier employer's address) were left untouched; rewriting published
  history wasn't requested and is destructive.
- Confirmed via `git log -p --all` and a tree-wide grep: no secrets, no
  ex-employer name/domain anywhere in tracked history or the working tree.
- Repo was already `PUBLIC` on GitHub going into this — this stage was
  about hygiene, not the visibility flip itself.

**Next up: Stage 1** — package restructure (`src/bounded/` namespace),
lint/type config, pre-commit, CI, reproducible Docker build.
