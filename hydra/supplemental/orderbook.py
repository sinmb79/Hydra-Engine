# hydra/supplemental/orderbook.py
import asyncio
import json
import time
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_INDICATOR_PREFIX = "hydra:indicator"
_ORDERBOOK_PREFIX = "hydra:orderbook"
_DEFAULT_INTERVAL = 30


class OrderBookPoller:
    def __init__(self, redis_client, interval_sec: int = _DEFAULT_INTERVAL):
        self._redis = redis_client
        self._interval = interval_sec

    async def _get_active_symbols(self) -> list[tuple[str, str]]:
        keys = await self._redis.keys(f"{_INDICATOR_PREFIX}:*")
        seen = set()
        result = []
        for key in keys:
            parts = key.split(":")
            if len(parts) < 5:
                continue
            market = parts[2]
            symbol = ":".join(parts[3:-1])
            if (market, symbol) not in seen:
                seen.add((market, symbol))
                result.append((market, symbol))
        return result

    def _get_exchange(self, market: str):
        import ccxt
        exchange_class = getattr(ccxt, market, None)
        if exchange_class is None:
            return None
        return exchange_class()

    def _fetch_one(self, market: str, symbol: str) -> dict | None:
        try:
            exchange = self._get_exchange(market)
            if exchange is None:
                return None
            ob = exchange.fetch_order_book(symbol, limit=5)
            bid = ob["bids"][0][0] if ob.get("bids") else None
            ask = ob["asks"][0][0] if ob.get("asks") else None
            if bid is None or ask is None:
                return None
            spread_pct = round((ask - bid) / ask * 100, 4)
            return {
                "bid": bid,
                "ask": ask,
                "spread_pct": spread_pct,
                "bids": ob["bids"][:5],
                "asks": ob["asks"][:5],
                "ts": int(time.time() * 1000),
            }
        except Exception as e:
            logger.warning("orderbook_fetch_error", market=market,
                           symbol=symbol, error=str(e))
            return None

    async def run(self) -> None:
        logger.info("orderbook_poller_started", interval=self._interval)
        while True:
            for market, symbol in await self._get_active_symbols():
                data = self._fetch_one(market, symbol)
                if data:
                    key = f"{_ORDERBOOK_PREFIX}:{market}:{symbol}"
                    await self._redis.set(key, json.dumps(data))
                    logger.debug("orderbook_cached", market=market, symbol=symbol)
            await asyncio.sleep(self._interval)


async def main() -> None:
    import redis.asyncio as aioredis
    from hydra.config.settings import get_settings
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    poller = OrderBookPoller(r)
    try:
        await poller.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
