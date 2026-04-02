# hydra/regime/engine.py
import asyncio
import json
import time
from hydra.regime.detector import RegimeDetector
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_CANDLE_CHANNEL = "hydra:candle:new"
_INDICATOR_PREFIX = "hydra:indicator"
_REGIME_PREFIX = "hydra:regime"


class RegimeEngine:
    def __init__(self, redis_client, detector: RegimeDetector):
        self._redis = redis_client
        self._detector = detector

    async def _handle_event(
        self, market: str, symbol: str, timeframe: str
    ) -> None:
        try:
            indicator_key = f"{_INDICATOR_PREFIX}:{market}:{symbol}:{timeframe}"
            raw = await self._redis.get(indicator_key)
            if raw is None:
                return
            indicators = json.loads(raw)
            close = float(indicators.get("close") or 0.0)
            regime = self._detector.detect(indicators, close)
            regime_key = f"{_REGIME_PREFIX}:{market}:{symbol}:{timeframe}"
            await self._redis.set(regime_key, json.dumps({
                "regime": regime,
                "detected_at": int(time.time() * 1000),
            }))
            logger.debug("regime_cached", market=market, symbol=symbol,
                         tf=timeframe, regime=regime)
        except Exception as e:
            logger.warning("regime_error", market=market, symbol=symbol,
                           tf=timeframe, error=str(e))

    async def cold_start(self) -> None:
        keys = await self._redis.keys(f"{_INDICATOR_PREFIX}:*")
        logger.info("regime_cold_start", count=len(keys))
        for key in keys:
            parts = key.split(":")
            if len(parts) < 5:
                continue
            market = parts[2]
            symbol = ":".join(parts[3:-1])
            timeframe = parts[-1]
            await self._handle_event(market, symbol, timeframe)

    async def run(self) -> None:
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(_CANDLE_CHANNEL)
                logger.info("regime_engine_subscribed", channel=_CANDLE_CHANNEL)
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                        await self._handle_event(
                            payload["market"], payload["symbol"], payload["timeframe"],
                        )
                    except Exception as e:
                        logger.warning("regime_subscribe_error", error=str(e))
            except Exception as e:
                logger.warning("regime_pubsub_reconnect", error=str(e))
                await asyncio.sleep(5)


async def main() -> None:
    import redis.asyncio as aioredis
    from hydra.config.settings import get_settings
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    detector = RegimeDetector()
    engine = RegimeEngine(redis_client=r, detector=detector)
    try:
        await engine.cold_start()
        await engine.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
