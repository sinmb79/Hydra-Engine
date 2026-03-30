from pybreaker import CircuitBreaker


def create_breaker(name: str, fail_max: int = 5, reset_timeout: int = 30) -> CircuitBreaker:
    """거래소/API별 독립 서킷 브레이커 생성."""
    return CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout, name=name)
