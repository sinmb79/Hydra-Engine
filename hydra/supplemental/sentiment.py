# hydra/supplemental/sentiment.py
import asyncio
import json
import time
import httpx
from hydra.logging.setup import get_logger

logger = get_logger(__name__)

_INDICATOR_PREFIX = "hydra:indicator"
_SENTIMENT_PREFIX = "hydra:sentiment"
_API_URL = "https://cryptopanic.com/api/v1/posts/"
_DEFAULT_INTERVAL = 300


class SentimentPoller:
    def __init__(self, redis_client, api_key: str = "",
                 interval_sec: int = _DEFAULT_INTERVAL):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._redis = redis_client
        self._api_key = api_key
        self._interval = interval_sec
        self._analyzer = SentimentIntensityAnalyzer()

    def _get_active_symbols(self) -> list[str]:
        keys = self._redis.keys(f"{_INDICATOR_PREFIX}:*")
        bases = set()
        for key in keys:
            parts = key.split(":")
            if len(parts) < 5:
                continue
            symbol = ":".join(parts[3:-1])
            base = symbol.split("/")[0] if "/" in symbol else symbol
            bases.add(base)
        return list(bases)

    async def _fetch_news(self, symbol: str) -> list[str]:
        try:
            params: dict = {"currencies": symbol, "public": "true"}
            if self._api_key:
                params["auth_token"] = self._api_key
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(_API_URL, params=params)
                resp.raise_for_status()
                results = resp.json().get("results", [])
                return [item["title"] for item in results if item.get("title")]
        except Exception as e:
            logger.warning("sentiment_fetch_error", symbol=symbol, error=str(e))
            return []

    def _score(self, headlines: list[str]) -> float:
        if not headlines:
            return 0.0
        scores = [self._analyzer.polarity_scores(h)["compound"] for h in headlines]
        return round(sum(scores) / len(scores), 4)

    async def run(self) -> None:
        logger.info("sentiment_poller_started", interval=self._interval)
        while True:
            for symbol in self._get_active_symbols():
                headlines = await self._fetch_news(symbol)
                score = self._score(headlines)
                key = f"{_SENTIMENT_PREFIX}:{symbol}"
                await self._redis.set(key, json.dumps({
                    "score": score,
                    "article_count": len(headlines),
                    "ts": int(time.time() * 1000),
                }))
                logger.debug("sentiment_cached", symbol=symbol, score=score)
            await asyncio.sleep(self._interval)


async def main() -> None:
    import os
    import redis.asyncio as aioredis
    from hydra.config.settings import get_settings
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    api_key = os.environ.get("CRYPTOPANIC_API_KEY", "")
    poller = SentimentPoller(r, api_key=api_key)
    try:
        await poller.run()
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
