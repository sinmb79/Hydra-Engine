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

    async def _get_active_symbols(self) -> list[str]:
        keys = await self._redis.keys(f"{_INDICATOR_PREFIX}:*")
        bases = set()
        for key in keys:
            parts = key.split(":")
            if len(parts) < 5:
                continue
            symbol = ":".join(parts[3:-1])
            base = symbol.split("/")[0] if "/" in symbol else symbol
            bases.add(base)
        return list(bases)

    async def _fetch_news(self, symbol: str) -> list[dict]:
        """Returns list of {title, published_at} dicts."""
        try:
            params: dict = {"currencies": symbol, "public": "true"}
            if self._api_key:
                params["auth_token"] = self._api_key
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(_API_URL, params=params)
                resp.raise_for_status()
                results = resp.json().get("results", [])
                return [
                    {"title": item["title"], "published_at": item.get("published_at")}
                    for item in results
                    if item.get("title")
                ]
        except Exception as e:
            logger.warning("sentiment_fetch_error", symbol=symbol, error=str(e))
            return []

    def _score_with_decay(self, articles: list[dict], market: str) -> float:
        from datetime import timezone
        from hydra.ml.sentiment import aggregate_sentiment
        from dateutil import parser as dtparser
        items = []
        for a in articles:
            raw_ts = a.get("published_at")
            try:
                pub = dtparser.parse(raw_ts).astimezone(timezone.utc) if raw_ts else None
            except Exception:
                pub = None
            score = self._analyzer.polarity_scores(a["title"])["compound"]
            if pub is not None:
                items.append({"score": score, "publish_time": pub})
        if not items:
            if not articles:
                return 0.0
            scores = [self._analyzer.polarity_scores(a["title"])["compound"] for a in articles]
            return round(sum(scores) / len(scores), 4)
        return round(aggregate_sentiment(items, market), 4)

    def _market_type(self, symbol: str) -> str:
        return "crypto"  # supplemental module handles crypto only

    async def run(self) -> None:
        logger.info("sentiment_poller_started", interval=self._interval)
        while True:
            for symbol in await self._get_active_symbols():
                articles = await self._fetch_news(symbol)
                score = self._score_with_decay(articles, self._market_type(symbol))
                key = f"{_SENTIMENT_PREFIX}:{symbol}"
                await self._redis.set(key, json.dumps({
                    "score": score,
                    "article_count": len(articles),
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
