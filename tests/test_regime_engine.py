# tests/test_regime_engine.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from hydra.regime.engine import RegimeEngine
from hydra.regime.detector import RegimeDetector


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.get = MagicMock(return_value=json.dumps({
        "BBB_5_2.0_2.0": 0.02, "ADX_14": 30.0, "EMA_50": 45000.0,
        "close": 50000.0,
        "calculated_at": 1000000
    }))
    r.set = AsyncMock()
    r.keys = MagicMock(return_value=["hydra:indicator:binance:BTC/USDT:1m"])
    r.pubsub = MagicMock()
    return r


@pytest.fixture
def engine(mock_redis):
    return RegimeEngine(redis_client=mock_redis, detector=RegimeDetector())


@pytest.mark.asyncio
async def test_handle_event_writes_regime(engine, mock_redis):
    await engine._handle_event("binance", "BTC/USDT", "1m")
    mock_redis.set.assert_called_once()
    key, value = mock_redis.set.call_args[0]
    assert key == "hydra:regime:binance:BTC/USDT:1m"
    data = json.loads(value)
    assert data["regime"] == "trending_up"
    assert "detected_at" in data


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
    await engine.cold_start()
    assert mock_redis.set.call_count == 2
