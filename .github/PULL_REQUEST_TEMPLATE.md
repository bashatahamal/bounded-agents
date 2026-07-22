## What and why

## Checklist

- [ ] `uv run ruff check src examples tests`
- [ ] `uv run ruff format --check src examples tests`
- [ ] `uv run mypy src examples`
- [ ] `uv run pytest -q`
- [ ] New logic in `bounded/` has unit tests; new network/LLM calls have a
      fixture-based test mocking them (see `tests/integration/test_fetchers.py`)
- [ ] If this is a kit change, it doesn't leak `company_research`-specific
      assumptions into `src/bounded/`
