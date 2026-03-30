from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


def with_retry(func):
    """지수 백오프 + 지터 재시도 데코레이터 (최대 3회)."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
        reraise=True,
    )(func)
