# tests/test_supplemental_sentiment.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hydra.supplemental.sentiment import SentimentPoller


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.keys = MagicMock(return_value=["hydra:indicator:binance:BTC/USDT:1m"])
    r.set = AsyncMock()
    return r


def test_score_positive_headline():
    r = MagicMock()
    poller = SentimentPoller(redis_client=r)
    score = poller._score(["Bitcoin is great and prices are rising strongly today!"])
    assert score > 0.0


def test_score_empty_headlines_returns_zero():
    r = MagicMock()
    poller = SentimentPoller(redis_client=r)
    score = poller._score([])
    assert score == 0.0


@pytest.mark.asyncio
async def test_fetch_news_returns_headlines():
    r = MagicMock()
    poller = SentimentPoller(redis_client=r, api_key="test_key")
    mock_response = {
        "results": [
            {"title": "Bitcoin price rises strongly"},
            {"title": "Market looks very bullish today"},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        headlines = await poller._fetch_news("BTC")
    assert len(headlines) == 2
    assert "Bitcoin price rises strongly" in headlines


@pytest.mark.asyncio
async def test_run_writes_redis(mock_redis):
    poller = SentimentPoller(redis_client=mock_redis)
    poller._fetch_news = AsyncMock(return_value=["Bitcoin is surging higher today!"])
    with patch("hydra.supplemental.sentiment.asyncio.sleep",
               side_effect=asyncio.CancelledError):
        try:
            await poller.run()
        except asyncio.CancelledError:
            pass
    assert mock_redis.set.call_count >= 1
    key, value = mock_redis.set.call_args_list[0][0]
    assert key == "hydra:sentiment:BTC"
    data = json.loads(value)
    assert "score" in data
    assert "article_count" in data
    assert data["article_count"] == 1
