.PHONY: install test lint format typecheck check run docker-build docker-up clean

install:
	uv sync --extra dev
	uv run pre-commit install

test:
	uv run pytest -q

lint:
	uv run ruff check src examples tests

format:
	uv run ruff format src examples tests

typecheck:
	uv run mypy src examples

check: lint typecheck test
	uv run ruff format --check src examples tests

run:
	uv run searchapp $(SPREADSHEET_ID)

docker-build:
	docker build -t bounded-agents .

docker-up:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache
