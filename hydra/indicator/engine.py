import asyncio
import json
from hydra.data.storage.base import OhlcvStore
from hydra.indicator.calculator import IndicatorCalculator
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_CHANNEL = "hydra:candle:new"
_KEY_PREFIX = "hydra:indicator"


class IndicatorEngine:
    def __init__(
        self,
        store: OhlcvStore,
        redis_client,
        calculator: IndicatorCalculator,
    ):
        self._store = store
        self._redis = redis_client
        self._calculator = calculator

    async def _handle_event(
        self, market: str, symbol: str, timeframe: str
    ) -> None:
        """Compute indicators for one (market, symbol, timeframe) and cache in Redis."""
        try:
            candles = await self._store.query(market, symbol, timeframe, limit=250)
            result = self._calculator.compute(candles)
            if not result:
                return
            key = f"{_KEY_PREFIX}:{market}:{symbol}:{timeframe}"
            await self._redis.set(key, json.dumps(result))
            logger.debug("indicator_cached", market=market, symbol=symbol, tf=timeframe)
        except Exception as e:
            logger.warning(
                "indicator_error",
                market=market, symbol=symbol, tf=timeframe, error=str(e),
            )

    async def cold_start(self) -> None:
        """On startup, compute indicators for all symbols already in the DB."""
        symbols = await self._store.get_symbols()
        logger.info("indicator_cold_start", count=len(symbols))
        for row in symbols:
            await self._handle_event(row["market"], row["symbol"], row["timeframe"])

    async def run(self) -> None:
        """Subscribe to hydra:candle:new and process events, with reconnect on disconnect."""
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(_CHANNEL)
                logger.info("indicator_engine_subscribed", channel=_CHANNEL)
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                        await self._handle_event(
                            payload["market"], payload["symbol"], payload["timeframe"]
                        )
                    except Exception as e:
                        logger.warning("indicator_subscribe_error", error=str(e))
            except Exception as e:
                logger.warning("indicator_pubsub_reconnect", error=str(e))
                await asyncio.sleep(5)


async def main() -> None:
    import redis.asyncio as aioredis
    from hydra.data.storage import create_store
    from hydra.config.settings import get_settings

    settings = get_settings()
    store = create_store()
    await store.init()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    calculator = IndicatorCalculator()
    engine = IndicatorEngine(store=store, redis_client=r, calculator=calculator)
    try:
        await engine.cold_start()
        await engine.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
