import pytest
from pybreaker import CircuitBreakerError
from hydra.resilience.circuit_breaker import create_breaker


def failing_fn():
    raise ConnectionError("exchange down")


def test_breaker_open_after_failures():
    breaker = create_breaker("test", fail_max=3, reset_timeout=60)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            breaker.call(failing_fn)
    # 3번째 실패에서 circuit이 open된다
    with pytest.raises(CircuitBreakerError):
        breaker.call(failing_fn)
    # circuit이 open되었으므로 이후 호출도 CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        breaker.call(failing_fn)


def test_breaker_passes_success():
    breaker = create_breaker("test2", fail_max=5, reset_timeout=60)
    result = breaker.call(lambda: "ok")
    assert result == "ok"
