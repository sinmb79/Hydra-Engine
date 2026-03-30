import asyncio
import json
import subprocess

from pybreaker import CircuitBreaker

from hydra.exchange.base import BaseExchange
from hydra.resilience.circuit_breaker import create_breaker
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

VALID_LEVERAGE = range(1, 126)  # 1x ~ 125x


class CryptoExchange(BaseExchange):
    """ccxt CLI를 subprocess로 호출. 서킷 브레이커 적용."""

    def __init__(self, exchange_id: str, breaker: CircuitBreaker | None = None, is_futures: bool = False):
        self.exchange_id = exchange_id
        self.is_futures = is_futures
        self._breaker = breaker or create_breaker(f"crypto:{exchange_id}")

    async def _run(self, args: list[str]) -> dict:
        cmd = ["ccxt", self.exchange_id] + args + ["--json"]
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: self._breaker.call(subprocess.check_output, cmd, text=True, timeout=15),
        )
        return json.loads(raw)

    async def get_balance(self) -> dict:
        return await self._run(["fetchBalance"])

    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float | None = None) -> dict:
        args = ["createOrder", symbol, order_type, side, str(qty)]
        if price:
            args.append(str(price))
        return await self._run(args)

    async def cancel_order(self, order_id: str) -> dict:
        return await self._run(["cancelOrder", order_id])

    async def cancel_all(self) -> list:
        result = await self._run(["cancelAllOrders"])
        return result if isinstance(result, list) else []

    async def get_positions(self) -> list:
        result = await self._run(["fetchPositions"])
        return result if isinstance(result, list) else []

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        """선물 레버리지 설정. 현물 모드에서는 no-op."""
        if not self.is_futures:
            logger.debug("set_leverage_skipped_spot", exchange=self.exchange_id, symbol=symbol)
            return
        if leverage not in VALID_LEVERAGE:
            raise ValueError(f"레버리지는 1~125 사이여야 합니다. 입력값: {leverage}")
        await self._run(["setLeverage", str(leverage), symbol])
        logger.info("leverage_set", exchange=self.exchange_id, symbol=symbol, leverage=leverage)
