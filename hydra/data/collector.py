"""OHLCV data collector — fetches candles via ccxt and persists them."""
import asyncio
import json
from pathlib import Path

import ccxt.async_support as ccxt
import redis.asyncio as aioredis
import yaml

from hydra.config.markets import MarketManager
from hydra.config.settings import get_settings
from hydra.data.storage import create_store
from hydra.data.storage.base import Candle
from hydra.logging.setup import configure_logging, get_logger

logger = get_logger(__name__)

_CCXT_ID = {
    "binance": "binance",
    "upbit": "upbit",
    "hl": "hyperliquid",
}

_TIMEFRAME_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}

_POLL_INTERVAL = 60  # seconds


def _load_data_config() -> dict:
    p = Path("config/data.yaml")
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}


_CCXT_OPTIONS = {
    "timeout": 15000,  # 15s per request
    "enableRateLimit": True,
}


async def _fetch_and_store(ex, market: str, symbol: str, timeframe: str, store, redis_client, since: int | None):
    try:
        raw = await ex.fetch_ohlcv(symbol, timeframe, since=since, limit=500)
        if not raw:
            return
        tf_ms = _TIMEFRAME_MS.get(timeframe, 60_000)
        candles = [
            Candle(
                market=market,
                symbol=symbol,
                timeframe=timeframe,
                open_time=int(r[0]),
                open=float(r[1]),
                high=float(r[2]),
                low=float(r[3]),
                close=float(r[4]),
                volume=float(r[5]),
                close_time=int(r[0]) + tf_ms - 1,
            )
            for r in raw
            if r[1] is not None
        ]
        await store.upsert(candles)
        logger.info("candles_upserted", market=market, symbol=symbol, timeframe=timeframe, count=len(candles))
        await redis_client.publish(
            "hydra:candle:new",
            json.dumps({"market": market, "symbol": symbol, "timeframe": timeframe}),
        )
    except Exception as exc:
        logger.error("fetch_failed", market=market, symbol=symbol, timeframe=timeframe, error=str(exc))


async def collect_once(store, market_manager: MarketManager, data_cfg: dict, redis_client=None) -> None:
    # 마켓별 exchange 인스턴스 공유 (load_markets 한 번만 호출)
    exchanges: dict[str, object] = {}
    try:
        for market, cfg in data_cfg.items():
            if not market_manager.is_active(market):
                continue
            exchange_id = _CCXT_ID.get(market)
            if exchange_id is None:
                continue
            if exchange_id not in exchanges:
                ex_cls = getattr(ccxt, exchange_id, None)
                if ex_cls is None:
                    logger.warning("ccxt_exchange_not_found", exchange=exchange_id)
                    continue
                exchanges[exchange_id] = ex_cls(_CCXT_OPTIONS)

        tasks = []
        for market, cfg in data_cfg.items():
            if not market_manager.is_active(market):
                continue
            exchange_id = _CCXT_ID.get(market)
            if exchange_id not in exchanges:
                continue
            ex = exchanges[exchange_id]
            for symbol in cfg.get("symbols", []):
                for timeframe in cfg.get("timeframes", ["1h"]):
                    tasks.append(
                        _fetch_and_store(ex, market, symbol, timeframe, store, redis_client, since=None)
                    )
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        for ex in exchanges.values():
            try:
                await ex.close()
            except Exception:
                pass


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("collector_starting")

    store = create_store()
    await store.init()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)

    market_manager = MarketManager()
    data_cfg = _load_data_config()

    try:
        while True:
            await collect_once(store, market_manager, data_cfg, redis_client=r)
            await asyncio.sleep(_POLL_INTERVAL)
    finally:
        await store.close()
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
