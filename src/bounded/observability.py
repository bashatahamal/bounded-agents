from __future__ import annotations

import os

import structlog


def configure_logging() -> None:
    """Configure structlog with ISO timestamps and JSON output.

    Call once, at process start (e.g. top of a CLI's `main()`) -- not at
    import time, so importing a module never has the side effect of
    reconfiguring global logging.
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )


def maybe_wrap_openai(client):
    """Wrap an OpenAI client with LangSmith tracing if LangSmith is configured.

    Returns the client unchanged if `langsmith` isn't installed or neither
    `LANGSMITH_API_KEY` nor `LANGCHAIN_API_KEY` is set. Tracing is strictly
    additive -- nothing in `bounded` requires it to run.
    """
    if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
        return client
    try:
        from langsmith.wrappers import wrap_openai
    except ImportError:
        return client
    return wrap_openai(client)
