# syntax=docker/dockerfile:1

# --- builder ---------------------------------------------------------------
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependency layer: cached as long as pyproject.toml / uv.lock don't change,
# independent of application source changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --extra dev

# Now the actual source, then install the project itself.
COPY src ./src
COPY examples ./examples
COPY README.md langgraph.json ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra dev

# --- runtime -----------------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /app app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 1024

# Runs the LangGraph dev server for interactive tracing/debugging (see
# docs/DESIGN.md, "Observability"). For a plain batch run against a
# spreadsheet instead, override the command: `docker run ... searchapp <id>`.
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "1024", "--no-browser"]
