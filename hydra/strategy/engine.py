# hydra/strategy/engine.py
import asyncio
import json
import os
from hydra.strategy.signal import Signal, SignalGenerator
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_CANDLE_CHANNEL = "hydra:candle:new"
_INDICATOR_PREFIX = "hydra:indicator"
_REGIME_PREFIX = "hydra:regime"
_SIGNAL_PREFIX = "hydra:signal"


class StrategyEngine:
    def __init__(
        self,
        redis_client,
        generator: SignalGenerator,
        dry_run: bool = True,
        order_queue=None,
        risk_engine=None,
        trade_amount_usd: float = 100.0,
    ):
        self._redis = redis_client
        self._generator = generator
        self._dry_run = dry_run
        self._order_queue = order_queue
        self._risk_engine = risk_engine
        self._trade_amount_usd = trade_amount_usd

    async def _handle_event(
        self, market: str, symbol: str, timeframe: str
    ) -> None:
        try:
            raw_indicator = await self._redis.get(
                f"{_INDICATOR_PREFIX}:{market}:{symbol}:{timeframe}"
            )
            if raw_indicator is None:
                return
            indicators = json.loads(raw_indicator)

            raw_regime = await self._redis.get(
                f"{_REGIME_PREFIX}:{market}:{symbol}:{timeframe}"
            )
            if raw_regime is None:
                return
            regime = json.loads(raw_regime).get("regime", "ranging")

            close = float(indicators.get("close") or 0.0)
            signal = self._generator.generate(indicators, regime, close)

            from hydra.engine.interfaces import (
                SizingParams, regime_str_to_probabilities, compute_regime_adjusted_size
            )
            regime_probs = regime_str_to_probabilities(regime)
            sizing = SizingParams(base_size=self._trade_amount_usd)
            effective_size = compute_regime_adjusted_size(regime_probs, sizing)

            await self._redis.set(
                f"{_SIGNAL_PREFIX}:{market}:{symbol}:{timeframe}",
                json.dumps({
                    "signal": signal.signal,
                    "reason": signal.reason,
                    "price": signal.price,
                    "ts": signal.ts,
                    "effective_size": round(effective_size, 4),
                }),
            )
            logger.debug("signal_cached", market=market, symbol=symbol,
                         tf=timeframe, signal=signal.signal, reason=signal.reason,
                         effective_size=round(effective_size, 4))

            if signal.signal in ("BUY", "SELL") and not self._dry_run:
                await self._submit_order(market, symbol, signal, effective_size)

        except Exception as e:
            logger.warning("strategy_error", market=market, symbol=symbol,
                           tf=timeframe, error=str(e))

    async def _submit_order(self, market: str, symbol: str, signal: Signal, effective_size: float | None = None) -> None:
        from hydra.core.order_queue import OrderRequest
        allowed, reason = self._risk_engine.check_order_allowed(market, symbol, 0.0)
        if not allowed:
            logger.info("order_blocked_by_risk", market=market, symbol=symbol,
                        reason=reason)
            return
        order = OrderRequest(
            market=market,
            symbol=symbol,
            side="buy" if signal.signal == "BUY" else "sell",
            order_type="market",
            amount=effective_size if effective_size is not None else self._trade_amount_usd,
        )
        result = await self._order_queue.submit(order)
        logger.info("order_submitted", market=market, symbol=symbol,
                    signal=signal.signal, order_id=result.order_id)

    async def cold_start(self) -> None:
        keys = await self._redis.keys(f"{_INDICATOR_PREFIX}:*")
        logger.info("strategy_cold_start", count=len(keys))
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
                logger.info("strategy_engine_subscribed", channel=_CANDLE_CHANNEL)
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                        await self._handle_event(
                            payload["market"], payload["symbol"], payload["timeframe"],
                        )
                    except Exception as e:
                        logger.warning("strategy_subscribe_error", error=str(e))
            except Exception as e:
                logger.warning("strategy_pubsub_reconnect", error=str(e))
                await asyncio.sleep(5)


async def main() -> None:
    import redis.asyncio as aioredis
    from hydra.config.settings import get_settings
    settings = get_settings()
    dry_run = os.environ.get("STRATEGY_DRY_RUN", "true").lower() != "false"
    trade_amount = float(os.environ.get("STRATEGY_TRADE_AMOUNT_USD", "100"))

    r = aioredis.from_url(settings.redis_url, decode_responses=True)

    order_queue = None
    risk_engine = None
    if not dry_run:
        from hydra.core.order_queue import OrderQueue
        from hydra.core.risk_engine import RiskEngine
        from hydra.core.position_tracker import PositionTracker
        position_tracker = PositionTracker(r)
        risk_engine = RiskEngine(r, position_tracker)
        order_queue = OrderQueue(r, risk_engine, position_tracker, exchanges={})

    generator = SignalGenerator()
    engine = StrategyEngine(
        redis_client=r,
        generator=generator,
        dry_run=dry_run,
        order_queue=order_queue,
        risk_engine=risk_engine,
        trade_amount_usd=trade_amount,
    )
    try:
        await engine.cold_start()
        await engine.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
