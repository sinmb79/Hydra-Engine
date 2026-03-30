import asyncio
import time


class TokenBucketRateLimiter:
    """거래소별 API 호출 제한. 우선순위: 0=주문, 1=시세, 2=조회."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens/second
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, priority: int = 2, tokens: int = 1) -> None:
        async with self._lock:
            self._refill()
            while self._tokens < tokens:
                wait = (tokens - self._tokens) / self.rate
                await asyncio.sleep(wait)
                self._refill()
            self._tokens -= tokens

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now
