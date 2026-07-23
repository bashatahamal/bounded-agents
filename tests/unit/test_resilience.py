import pytest

from bounded.resilience import with_retry


class _FlakyThenOK:
    def __init__(self, fail_times: int, exc: type[Exception] = ValueError):
        self.fail_times = fail_times
        self.calls = 0
        self.exc = exc

    def __call__(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc("transient")
        return "ok"


def _fast_retry(**kwargs):
    return with_retry(min_wait=0.001, max_wait=0.002, **kwargs)


def test_with_retry_succeeds_after_transient_failures():
    flaky = _FlakyThenOK(fail_times=2)
    wrapped = _fast_retry(attempts=3)(flaky)

    assert wrapped() == "ok"
    assert flaky.calls == 3


def test_with_retry_reraises_after_exhausting_attempts():
    flaky = _FlakyThenOK(fail_times=99)
    wrapped = _fast_retry(attempts=3)(flaky)

    with pytest.raises(ValueError):
        wrapped()
    assert flaky.calls == 3


def test_with_retry_does_not_retry_unmatched_exception_types():
    flaky = _FlakyThenOK(fail_times=99, exc=KeyError)
    wrapped = _fast_retry(attempts=5, retry_on=(ValueError,))(flaky)

    with pytest.raises(KeyError):
        wrapped()
    assert flaky.calls == 1
