import asyncio
import json
import subprocess

from hydra.exchange.base import BaseExchange
from hydra.logging.setup import get_logger

logger = get_logger(__name__)


class PolymarketExchange(BaseExchange):
    """polymarket-cli subprocess 래핑."""

    async def _run(self, args: list[str]) -> dict:
        cmd = ["polymarket"] + args + ["--json"]
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: subprocess.check_output(cmd, text=True, timeout=15),
        )
        return json.loads(raw)

    async def get_balance(self) -> dict:
        return await self._run(["balance"])

    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float | None = None) -> dict:
        args = ["order", "create", "--market", symbol, "--side", side, "--amount", str(qty)]
        if price:
            args += ["--price", str(price)]
        return await self._run(args)

    async def cancel_order(self, order_id: str) -> dict:
        return await self._run(["order", "cancel", "--id", order_id])

    async def cancel_all(self) -> list:
        result = await self._run(["order", "cancel-all"])
        return result if isinstance(result, list) else []

    async def get_positions(self) -> list:
        result = await self._run(["positions"])
        return result if isinstance(result, list) else []
