# tests/test_strategy_engine.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from hydra.strategy.engine import StrategyEngine
from hydra.strategy.signal import SignalGenerator


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.get = MagicMock(side_effect=lambda key: (
        json.dumps({"EMA_9": 1.1, "EMA_20": 1.0, "RSI_14": 55.0, "close": 50000.0})
        if ":indicator:" in key
        else json.dumps({"regime": "trending_up"})
    ))
    r.set = AsyncMock()
    r.keys = MagicMock(return_value=["hydra:indicator:binance:BTC/USDT:1m"])
    r.pubsub = MagicMock()
    return r


@pytest.fixture
def engine(mock_redis):
    return StrategyEngine(
        redis_client=mock_redis,
        generator=SignalGenerator(),
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_handle_event_writes_signal(engine, mock_redis):
    await engine._handle_event("binance", "BTC/USDT", "1m")
    mock_redis.set.assert_called_once()
    key, value = mock_redis.set.call_args[0]
    assert key == "hydra:signal:binance:BTC/USDT:1m"
    data = json.loads(value)
    assert data["signal"] == "BUY"
    assert "reason" in data
    assert "price" in data
    assert "ts" in data


@pytest.mark.asyncio
async def test_handle_event_skips_when_no_indicator(engine, mock_redis):
    mock_redis.get = MagicMock(return_value=None)
    await engine._handle_event("binance", "BTC/USDT", "1m")
    mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_does_not_raise(engine, mock_redis):
    mock_redis.get = MagicMock(side_effect=RuntimeError("redis error"))
    await engine._handle_event("binance", "BTC/USDT", "1m")


@pytest.mark.asyncio
async def test_cold_start_processes_all_keys(engine, mock_redis):
    mock_redis.keys = MagicMock(return_value=[
        "hydra:indicator:binance:BTC/USDT:1m",
        "hydra:indicator:upbit:BTC/KRW:1h",
    ])
    mock_redis.get = MagicMock(side_effect=lambda key: (
        json.dumps({"EMA_9": 1.1, "EMA_20": 1.0, "RSI_14": 55.0, "close": 50000.0})
        if ":indicator:" in key
        else json.dumps({"regime": "trending_up"})
    ))
    await engine.cold_start()
    assert mock_redis.set.call_count == 2
