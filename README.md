# bounded-agents

**Deterministic orchestration for LLM pipelines: authority in code, phrasing in the LLM.**

Most "agentic" pipelines let the LLM decide what's true. This kit doesn't: source
priority, what counts as a gap, and what's allowed to fill it are all decided in
code before the LLM ever sees the data. The LLM's job is synthesis and
judgment inside boundaries it can't step outside of — not deciding what to trust.

`bounded` covers all three layers of a simple rule: **who decides the next
step?** Nobody → a **Tool** (`Capability`), one input in, one output out.
The code → a **Workflow** (a LangGraph pipeline with fixed step order). The
LLM → an **Agent** (`bounded.agent`, a tool-calling loop that produces an
auditable conversation). Only the third one hands the LLM control of *flow*
— and even there, the loop itself stays bounded: a hard step limit, a
scope guard that runs in code before every tool call, every failure
captured instead of crashing.

Two things live here:

- **`src/bounded/`** — the reusable kit. Define a typed `Capability` once,
  run it as a CLI command, a LangGraph node, an MCP tool, or a tool an
  `Agent` can call — without rewriting the logic four times. Also ships the
  arbitration/judge pattern, a Context Pack builder, and a provenance-ranked
  memory store, all generic and swappable.
- **Two reference examples**: `examples/company_research/` (a Workflow — a
  LangGraph pipeline that researches a company and writes a summary to
  Google Sheets) and `examples/task_assistant/` (an Agent — a CLI chat
  assistant that manages tasks and remembers preferences). Neither is an
  abstraction exercise; both are what prove the kit holds together.

**This is a library, not a platform.** There's no service to deploy, no
messaging gateway, no scheduler, no skill marketplace — `bounded` has none
of that, on purpose. You `import bounded` into an application that already
has its own bot, its own control loop, its own scheduler, and add one
scoped, auditable capability to it. If what you actually want is a
standalone autonomous assistant with built-in Telegram/Discord/WhatsApp
gateways and a skill registry, a platform like
[OpenClaw](https://github.com/orgs/openclaw/repositories) or
[Hermes Agent](https://github.com/nousresearch/hermes-agent) is the better
tool for that job — see [`docs/COMPARISON.md`](docs/COMPARISON.md) for an
honest side-by-side instead of a hand-wave.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the design rationale, and
[`docs/PROGRESS.md`](docs/PROGRESS.md) for how this repo got here (including
which parts of the Agent layer are unverified against a real LLM — read
that before relying on it).

![LangGraph pipeline](assets/main-graph.png)

## Why "bounded"

An LLM judge in this pipeline can flag a gap and recommend which
already-approved secondary source should fill it. It cannot introduce a new
source, invent a fact, or merge conflicting claims — that's enforced by
`bounded.arbitration` and `bounded.judge`, not by prompting alone. If the
judge's output can't be parsed, the pipeline falls back to the deterministic
selection instead of guessing. Authority never depends on the LLM behaving.

## Quickstart

```bash
git clone https://github.com/bashatahamal/bounded-agents.git
cd bounded-agents
uv sync
cp .env.sample .env   # fill in your API keys — see below
uv run searchapp <spreadsheet_id>
```

`uv run searchapp --help` works with **no credentials set at all** — nothing
in this repo touches the network or reads settings until you actually invoke
a pipeline.

### Prerequisites

- Python ≥ 3.12
- [`uv`](https://github.com/astral-sh/uv)
- OpenAI API key, Tavily API key, Serper API key
- A Google Sheets service account (only needed for the Sheets sink — see
  [Sinks](#sinks-swap-the-output) below for alternatives that need none of
  this)

## The kit (`src/bounded/`)

| Module | What it is |
| --- | --- |
| `capability.py` | `Capability[TIn: BaseModel, TOut: BaseModel]` — one typed input, one typed output, one `run` callable. Register once, run four ways. |
| `registry.py` | Name → `Capability` lookup. |
| `adapters/cli.py` | Turns a Capability's input model into an argparse subcommand automatically. |
| `adapters/langgraph.py` | Wraps a Capability as a dict-in/dict-out LangGraph node. Also has `safe_merge`, a generic None-safe/type-aware state-merge reducer for parallel graph branches. |
| `adapters/mcp.py` | Describes a Capability as an MCP tool (name, description, JSON schemas, handler) — no MCP SDK dependency required. |
| `arbitration.py` | `Source` + `select()` — deterministic primary/secondary source selection, given sources in priority order and a `field -> keywords` coverage map. |
| `judge.py` | `parse_judge_output()` / `run_bounded_judge()` — defensively parses an LLM judge's raw text (strips code fences, smart quotes, trailing commas) and drops any field the judge invented outside the allowed schema. Raises `JudgeError` rather than ever fabricating a result. |
| `sinks/` | `Sink` protocol + `GoogleSheetsSink`, `CsvSink`, `JsonlSink`. Swap the output target without touching pipeline logic. |
| `llm/` | `LLMProvider` protocol (`complete()`) + `ToolCallingLLM` protocol (`chat()`) + `OpenAIProvider`, which implements both. |
| `agent.py` | `Agent` — an LLM-driven tool-calling loop over a list of `Capability`s. Bounded by a hard `max_steps` cutoff, an optional `guard` callable that can reject a tool call in code (`ScopeError`), and every failure (bad arguments, unknown tool, the tool's own exception) captured as a `ToolCall.error` instead of ever crashing. Produces an auditable `Thread`. |
| `adapters/agent.py` | `as_openai_tool()` — converts a `Capability` into OpenAI's tool-calling schema, the fourth surface alongside CLI/LangGraph/MCP. |
| `context.py` | `ContextSource` + `build_context_pack()` — combines prioritized text blocks into one preface; over a `max_chars` budget it drops whole lowest-priority sources, never truncates mid-source. |
| `memory.py` | `Provenance`-ranked durable memory (`human_manual > human_feedback > llm_inferred`), `JsonlMemoryStore`, and `distill()` — asks an LLM to extract durable rules from feedback text, reusing `judge.py`'s defensive-parsing discipline. |
| `json_repair.py` | The JSON-cleanup helpers (`strip_markdown_fences`, `normalize_quotes`, `remove_trailing_commas`, `extract_json_object`) shared by `judge.py` and `memory.py`. |
| `credentials.py` | Loads a JSON credential from a file path, base64, or raw JSON string — fails loudly instead of ever silently returning `{}`. |
| `resilience.py` | `with_retry()` — a thin `tenacity` wrapper for exponential-backoff retries on flaky network/LLM calls. |
| `observability.py` | structlog config + opt-in LangSmith tracing (only activates if `LANGSMITH_API_KEY`/`LANGCHAIN_API_KEY` is set). |

None of this is company-research-specific. A different pipeline (incident
triage, product research, anything that needs "pick an authoritative source,
optionally ask an LLM to fill gaps under supervision") can depend on
`bounded` directly and bring its own example.

## The example (`examples/company_research/`)

Website, LinkedIn, and four search facets (general / founder / finance /
news) fetch in parallel and fan into `validate` → `select_sources`, which
picks one primary source and ranks the rest as secondary (see the graph
diagram above). `select_sources` conditionally routes to `judge` — only when
there's a coverage gap *and* a secondary source that could plausibly fill it
— before `build_input` → `summarize` produces the final write.

- **Sources are fetched in parallel**; authority is applied only at
  selection time (website > search > LinkedIn, in code — see
  `nodes/validate.py`).
- **The judge is invoked conditionally** — only when there's a gap *and* a
  secondary source that could plausibly fill it. If nothing needs enriching,
  the LLM never sees the judge prompt at all.
- **Everything degrades gracefully**: a failed fetch, an unparsable judge
  response, a missing field — none of it crashes the run. The pipeline
  either narrows what it claims or explicitly marks a gap; it never guesses
  silently.

Full rationale: [`docs/DESIGN.md`](docs/DESIGN.md).

### Running it

```bash
uv run searchapp <spreadsheet_id>
uv run searchapp <spreadsheet_id> --input-worksheet Names --output-worksheet "Review Company"
```

**Input sheet** — one column, `Company Name`:

| Company Name |
| --- |
| Traveloka |
| Gojek |

**Output sheet** — written to `Review Company` by default:

| Company | Summary |
| --- | --- |
| Traveloka | **Company Overview**: Traveloka is ... |
| Gojek | **Company Overview**: Gojek is ... |

### Sinks: swap the output

`CompanyResearch` currently wires up `GoogleSheetsSink`, but the graph itself
returns a plain `dict` — swapping in `CsvSink` or `JsonlSink` (no Google
credentials needed) means changing one constructor call, not the pipeline:

```python
from bounded.sinks import CsvSink

sink = CsvSink("out/")
sink.write(["Company", "Summary"], [[name, summary]], destination="companies")
```

## The agent example (`examples/task_assistant/`)

A CLI chat assistant with four tools (`add_task`, `list_tasks`,
`complete_task`, `remember_preference`) over a JSON-file task store and a
`JsonlMemoryStore`. This is where `bounded.agent`, `bounded.context`, and
`bounded.memory` actually come together:

```bash
uv run task-assistant
```

```
> add a task to buy milk tomorrow
Added "buy milk" for 2026-07-23.
> remember that i usually check tasks in the evening
Noted (memory: preferences/human_manual).
```

- **The LLM decides which tool to call**, unlike `company_research`'s fixed
  graph — that's the actual difference between a Workflow and an Agent.
- **`remember_preference` writes with `Provenance.HUMAN_MANUAL`** — the
  user explicitly asked to be remembered. `bounded.memory.distill()` (for
  turning raw feedback into `Provenance.LLM_INFERRED` rules) is available
  but intentionally not wired into this toy example — it's there for a
  domain that actually needs it, not forced in just to exercise it.
- **Every `build_agent()` call rebuilds the system prompt from current
  memory** via `build_context_pack()` — what you tell it to remember in one
  session shows up in the next process's Context Pack, verified in
  `tests/integration/test_task_assistant_agent.py`, not just asserted.

**Prerequisite:** only `OPENAI_API_KEY` — no Tavily/Serper/Google Sheets
needed for this example.

**Not yet verified against a real model** — see
[`docs/PROGRESS.md`](docs/PROGRESS.md)'s Stage 5 entry. Run a real
conversation through `uv run task-assistant` before relying on this beyond
what the mocked tests cover.

## Observability: LangGraph Studio + LangSmith (optional)

```bash
cp .env.sample .env   # set LANGSMITH_API_KEY / LANGCHAIN_API_KEY too
docker compose up --build
```

Then open LangGraph Studio:

```
https://smith.langchain.com/studio/?baseUrl=http://0.0.0.0:1024
```

![LangGraph Studio](assets/langgraph-vis1.png)

Traces are node-level: fetch inputs, judge prompts/responses, token usage per
step. None of it is required to run the pipeline — see
`bounded.observability.maybe_wrap_openai`.

## Development

```bash
uv sync --extra dev
uv run pytest -q                          # 100 tests: kit unit tests, fixture-based
                                           # fetcher tests, and mocked end-to-end runs
                                           # for both examples
uv run ruff check src examples tests
uv run ruff format src examples tests
uv run mypy src examples
```

`.pre-commit-config.yaml` runs ruff automatically on commit:

```bash
uv run pre-commit install
```

CI (`.github/workflows/ci.yml`) runs the same checks on Python 3.12 and 3.13.

## License

[Apache-2.0](LICENSE).
