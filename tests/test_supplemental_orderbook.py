# tests/test_supplemental_orderbook.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hydra.supplemental.orderbook import OrderBookPoller


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.keys = MagicMock(return_value=[
        "hydra:indicator:binance:BTC/USDT:1m",
        "hydra:indicator:binance:ETH/USDT:1h",
    ])
    r.set = AsyncMock()
    return r


@pytest.fixture
def poller(mock_redis):
    return OrderBookPoller(redis_client=mock_redis, interval_sec=1)


def test_get_active_symbols_deduplicates(poller, mock_redis):
    mock_redis.keys = MagicMock(return_value=[
        "hydra:indicator:binance:BTC/USDT:1m",
        "hydra:indicator:binance:BTC/USDT:1h",
        "hydra:indicator:binance:ETH/USDT:1m",
    ])
    symbols = poller._get_active_symbols()
    assert ("binance", "BTC/USDT") in symbols
    assert ("binance", "ETH/USDT") in symbols
    assert len(symbols) == 2


def test_fetch_one_returns_orderbook(poller):
    mock_ob = {
        "bids": [[49998.0, 1.5], [49997.0, 2.0]],
        "asks": [[50002.0, 1.2], [50003.0, 1.8]],
    }
    mock_exchange = MagicMock()
    mock_exchange.fetch_order_book.return_value = mock_ob
    poller._get_exchange = MagicMock(return_value=mock_exchange)
    result = poller._fetch_one("binance", "BTC/USDT")
    assert result is not None
    assert result["bid"] == 49998.0
    assert result["ask"] == 50002.0
    assert "spread_pct" in result
    assert "ts" in result


def test_fetch_one_returns_none_on_error(poller):
    mock_exchange = MagicMock()
    mock_exchange.fetch_order_book.side_effect = Exception("connection error")
    poller._get_exchange = MagicMock(return_value=mock_exchange)
    result = poller._fetch_one("binance", "BTC/USDT")
    assert result is None


@pytest.mark.asyncio
async def test_run_writes_redis(poller, mock_redis):
    mock_ob = {
        "bids": [[49998.0, 1.5]],
        "asks": [[50002.0, 1.2]],
    }
    mock_exchange = MagicMock()
    mock_exchange.fetch_order_book.return_value = mock_ob
    poller._get_exchange = MagicMock(return_value=mock_exchange)
    with patch("hydra.supplemental.orderbook.asyncio.sleep",
               side_effect=asyncio.CancelledError):
        try:
            await poller.run()
        except asyncio.CancelledError:
            pass
    assert mock_redis.set.call_count == 2  # BTC/USDT and ETH/USDT
    key = mock_redis.set.call_args_list[0][0][0]
    assert key.startswith("hydra:orderbook:binance:")
    data = json.loads(mock_redis.set.call_args_list[0][0][1])
    assert "bid" in data
