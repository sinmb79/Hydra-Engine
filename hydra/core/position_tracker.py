import json
from typing import Optional

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

POSITIONS_KEY = "hydra:positions"


class PositionTracker:
    def __init__(self, redis_client):
        self._redis = redis_client

    def update(self, market: str, symbol: str, qty: float, avg_price: float, side: str, leverage: int = 1, mark_price: float | None = None) -> None:
        key = f"{POSITIONS_KEY}:{market}:{symbol}"
        data = {
            "qty": qty,
            "avg_price": avg_price,
            "side": side,
            "market": market,
            "symbol": symbol,
            "leverage": leverage,
            "mark_price": mark_price or avg_price,
        }
        self._redis.set(key, json.dumps(data))
        logger.info("position_updated", market=market, symbol=symbol, qty=qty, leverage=leverage)

    def get(self, market: str, symbol: str) -> Optional[dict]:
        key = f"{POSITIONS_KEY}:{market}:{symbol}"
        raw = self._redis.get(key)
        return json.loads(raw) if raw else None

    def get_all(self) -> list[dict]:
        keys = self._redis.keys(f"{POSITIONS_KEY}:*")
        result = []
        for k in keys:
            raw = self._redis.get(k)
            if raw:
                result.append(json.loads(raw))
        return result

    def clear(self, market: str, symbol: str) -> None:
        key = f"{POSITIONS_KEY}:{market}:{symbol}"
        self._redis.delete(key)
        logger.info("position_cleared", market=market, symbol=symbol)

    async def snapshot(self) -> dict:
        return {"positions": self.get_all()}
