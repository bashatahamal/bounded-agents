from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

T = TypeVar("T")


def with_retry(
    *,
    attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a flaky call (network, LLM) with exponential backoff.

    Defaults to 3 attempts and 1-10s exponential backoff, retrying on any
    Exception. Narrow `retry_on` to the specific transient errors a given
    integration raises (e.g. `requests.RequestException`) so a genuine bug
    fails fast instead of being retried three times and reraised anyway.
    """
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_on),
        reraise=True,
    )
