# Contributing

## Setup

```bash
uv sync --extra dev
uv run pre-commit install
```

## Before opening a PR

```bash
uv run ruff check src examples tests
uv run ruff format --check src examples tests
uv run mypy src examples
uv run pytest -q
```

CI runs the same four checks on Python 3.12 and 3.13 — a PR that fails any of
them locally will fail there too.

## Where things go

- **`src/bounded/`** is the reusable kit. Nothing in here should know
  anything about company research specifically — if you're adding logic
  that only makes sense for that example, it belongs in
  `examples/company_research/` instead.
- **`examples/company_research/`** is the reference implementation. Changes
  here should still exercise the kit's public surface (`bounded.arbitration`,
  `bounded.judge`, `bounded.sinks`, ...) rather than reimplementing it
  locally.
- **`docs/PROGRESS.md`** is a running log, not a changelog — if you're doing
  a substantial restructure, add an entry explaining what changed and why,
  the same way the rest of the file does.

## Tests

- Pure logic (anything in `bounded/` that doesn't touch a network) gets unit
  tests in `tests/unit/`.
- Anything that calls `requests`, an LLM, or a third-party client gets a
  fixture-based test in `tests/integration/` that mocks the call — see
  `tests/integration/test_fetchers.py` for the pattern.
- `tests/conftest.py`'s `_fake_credentials` fixture sets fake env vars and
  clears every `lru_cache`'d settings/client singleton before and after each
  test. If you add a new lazily-cached singleton, clear it there too, or
  tests will leak state across each other depending on run order.

## Commit messages

Explain *why*, not just *what* — the diff already shows what changed.
