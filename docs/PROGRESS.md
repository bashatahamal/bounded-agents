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

### Positioning: library vs. platform — done (2026-07-22)

Prompted by a direct question: why build this instead of adopting an
existing agent framework (OpenClaw, Hermes Agent)? Researched both for
real (not from memory) before answering — see the chat transcript around
this timestamp for sources. Conclusion, written down so it doesn't have to
be re-argued from scratch later: OpenClaw and Hermes Agent are self-hosted
*platforms* (their own process, messaging gateway, scheduler, skill
marketplace); `bounded` is a *library* with none of that, meant to be
imported into an app that already has its own control plane. Different
problems, not competing answers to the same one.

Added `docs/COMPARISON.md` — an honest side-by-side (what each actually
is, dependencies, autonomy model, license, maturity), plus a "when each is
the right call" section. Linked from the README intro, which now leads
with "this is a library, not a platform" instead of leaving that implicit.
Concrete numbers used instead of hand-waving: `src/bounded/` is ~1,180
LOC across 26 files, and its own runtime imports are just `pydantic`,
`openai` and `gspread` (both only needed if you use those specific
pieces), `tenacity`, and `structlog` — no Node.js, no messaging gateway,
no scheduler, no vector DB.

### CI verified green on push — 2026-07-22

The `workflow` OAuth scope (blocked back in the "Repo rename + push" entry
below) got refreshed, so the held-back `.github/workflows/ci.yml` commit
and the Stage 5 commit both pushed in one shot. That means CI actually ran
for the first time on real GitHub Actions runners rather than just
locally: both matrix jobs (Python 3.12 and 3.13, ubuntu-latest) passed --
ruff check, ruff format --check, mypy, and the full 100-test pytest suite,
all green, independent of this sandbox
(https://github.com/bashatahamal/bounded-agents/actions/runs/29909615695).
Also re-ran CI against PR #1 automatically (it targets `main` via
`pull_request` trigger) -- also green. This is real third-party
verification, unlike the Docker build in Stage 1 which is still only
eyeballed, never actually built.

### Stage 5 — Agent primitive — done (2026-07-22)

Added the third layer this repo was missing: today `bounded` covered Tool
(`Capability`) and Workflow (`examples/company_research`'s LangGraph
pipeline), both fully code-controlled. This adds **Agent** — the layer
where the LLM decides which tool to call, when, and how many times,
producing an auditable conversation rather than a single value. The
pattern (Context Pack, provenance-ranked memory, scope enforcement in
code, graceful degradation) is generalized from a real production agent's
architecture (not copied — only the shape, no code or domain specifics
came from that codebase), kept strictly domain-agnostic, and proven with a
new toy example, `examples/task_assistant`. Full design writeup and the
question this closes: `C:\Users\mhbrt\.claude\plans\structured-launching-hummingbird.md`.

**New in `src/bounded/`:**
- `agent.py` — `Agent`, `Thread`, `ToolCall`, `ScopeError`. The loop itself
  stays bounded even though the LLM controls flow inside it: a hard
  `max_steps` cutoff (never runs forever), an optional `guard` callable
  that runs in code before every tool call and can reject one via
  `ScopeError`, and every failure mode (bad arguments, unknown tool name,
  the tool's own exception, a guard rejection) captured as a
  `ToolCall.error` instead of ever propagating and crashing the
  conversation.
- `context.py` — `ContextSource` + `build_context_pack()`. Combines
  prioritized text blocks into one preface; over a `max_chars` budget it
  drops whole lowest-priority sources (a strict priority-ordered prefix),
  never truncates mid-source.
- `memory.py` — `Provenance` (`human_manual > human_feedback >
  llm_inferred`), `MemoryEntry`, `MemoryStore` protocol, `JsonlMemoryStore`
  (file-backed, same shape as `bounded.sinks.jsonl`), `distill()` (asks an
  LLM to extract durable rules from feedback text, reusing the same
  defensive JSON-parsing discipline as `bounded.judge` — returns `[]`
  rather than fabricating on unparseable output).
- `json_repair.py` — the JSON-cleanup helpers (`strip_markdown_fences`,
  `normalize_quotes`, `remove_trailing_commas`, `extract_json_object`,
  `clean_json_text`) factored out of `judge.py` once `memory.py` needed
  the identical logic — two real call sites justified the extraction;
  `judge.py` now imports from here instead of keeping its own copies.
- `adapters/agent.py` — `as_openai_tool()`, converting a `Capability` into
  OpenAI's tool-calling schema, the same pattern as `adapters/mcp.py`'s
  `as_mcp_tool()` just a different wire shape.
- `llm/base.py` — added `ToolCallingLLM` protocol (`chat(messages, tools)
  -> ChatResult`), `ChatResult`, `ToolCallRequest`, kept deliberately
  separate from `LLMProvider` (`judge.py` / `summarize.py` keep depending
  on the narrower `complete()` surface).
- `llm/openai_provider.py` — `OpenAIProvider` gained `chat()` implementing
  `ToolCallingLLM`, same client/retry/tracing setup as `complete()`, not a
  new class.

**New example, `examples/task_assistant/`:** a CLI chat agent
(`uv run task-assistant`) with four tools (`add_task`, `list_tasks`,
`complete_task`, `remember_preference`) backed by a JSON-file `TaskStore`
and a `JsonlMemoryStore`. `remember_preference` writes with
`Provenance.HUMAN_MANUAL` (the user explicitly asked to be remembered);
`bounded.memory.distill()` with `Provenance.LLM_INFERRED` is available for
inferred preferences but not wired into this toy example's flow — kept
for a future pass rather than forced in just to exercise it. Every
`build_agent()` call rebuilds the system prompt from current memory via
`build_context_pack()`, so what's remembered actually shows up in the
next process's `system_prompt` — verified directly in
`tests/integration/test_task_assistant_agent.py`, not just asserted.

**Explicitly not built** (per the plan): no Postgres/Redis, no
embedding-based memory dedup (exact-match only, documented as a known
gap), no bidirectional Telegram/Channel abstraction, no multi-provider
tool-calling. Nothing about `home_app` (device state, trip detection,
actual reminders) touches this repo — `home_app` will import `bounded` as
a library once this ships; the dependency direction only goes one way.

**Verification:**
- `uv run ruff check` / `ruff format --check` / `mypy src examples` /
  `pytest -q` — all clean. 100 tests total (was 62 before this stage):
  `test_agent.py` (loop happy path, step-limit cutoff, guard rejection,
  unknown tool, tool exception, invalid arguments, multi-turn thread
  continuation), `test_context.py` (priority ordering, budget-drops-whole-
  sources, never-truncates-mid-source, strict-prefix-not-bin-packing),
  `test_memory.py` (add/list roundtrip, scope filtering, provenance
  ranking, dedup incl. cross-scope non-dedup, persistence across store
  instances, `distill()` happy/malformed/partially-malformed paths),
  `test_json_repair.py`, `test_adapters_agent.py`, plus
  `test_task_assistant_tools.py` (all four tools, no LLM) and
  `test_task_assistant_agent.py` (two full mocked conversations end to
  end: add-a-task, and remember-a-preference-then-see-it-in-the-next-
  agent's-system-prompt).
- **Not verified**: an actual live run against real OpenAI tool-calling.
  No `OPENAI_API_KEY` is available in this sandbox (checked: no repo
  `.env`, nothing in the shell environment) — the plan's manual
  verification step (`uv run task-assistant`, a real conversation) could
  not be performed. What IS verified: `OPENAI_API_KEY=fake uv run
  task-assistant` starts the REPL and exits cleanly on EOF (proves
  `OpenAIProvider.__init__` doesn't make a network call, and the whole
  import/wiring chain works), and the mocked end-to-end tests above cover
  the actual tool-calling loop logic. Flagging this the same way the
  Docker build was flagged in Stage 1 -- **run a real conversation through
  `uv run task-assistant` with a genuine API key before treating this as
  fully proven.**

**Next up:** none planned in this repo for now. `home_app` picks this up
from here, privately, as its own next step.

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
