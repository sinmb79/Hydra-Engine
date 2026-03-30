# hydra/supplemental/events.py
import asyncio
import json
import httpx
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_EVENTS_KEY = "hydra:events:upcoming"
_API_URL = "https://api.coinmarketcal.com/v1/events"
_DEFAULT_INTERVAL = 3600


class EventCalendarPoller:
    def __init__(self, redis_client, api_key: str = "",
                 interval_sec: int = _DEFAULT_INTERVAL):
        self._redis = redis_client
        self._api_key = api_key
        self._interval = interval_sec

    async def _fetch(self) -> list[dict]:
        if not self._api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    _API_URL,
                    headers={"x-api-key": self._api_key},
                    params={"max": 10, "dateRangeEnd": "+24h"},
                )
                resp.raise_for_status()
                body = resp.json()
                events = []
                for item in body.get("body", []):
                    coins = item.get("coins") or []
                    symbol = coins[0].get("symbol", "") if coins else ""
                    events.append({
                        "title": item.get("title", ""),
                        "symbol": symbol,
                        "date_event": item.get("date_event", ""),
                        "source": "coinmarketcal",
                    })
                return events
        except Exception as e:
            logger.warning("events_fetch_error", error=str(e))
            return []

    async def run(self) -> None:
        logger.info("events_poller_started", interval=self._interval,
                    has_key=bool(self._api_key))
        while True:
            events = await self._fetch()
            await self._redis.set(_EVENTS_KEY, json.dumps(events))
            logger.debug("events_cached", count=len(events))
            await asyncio.sleep(self._interval)


async def main() -> None:
    import os
    import redis.asyncio as aioredis
    from hydra.config.settings import get_settings
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    api_key = os.environ.get("COINMARKETCAL_API_KEY", "")
    poller = EventCalendarPoller(r, api_key=api_key)
    try:
        await poller.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
