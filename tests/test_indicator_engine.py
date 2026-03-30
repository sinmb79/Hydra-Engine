import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from hydra.data.models import Candle
from hydra.indicator.engine import IndicatorEngine
from hydra.indicator.calculator import IndicatorCalculator


def _make_candles(n: int = 250) -> list[Candle]:
    candles = []
    price = 50000.0
    for i in range(n):
        close = price * (1 + (0.001 if i % 2 == 0 else -0.001))
        price = close
        candles.append(Candle(
            market="binance", symbol="BTC/USDT", timeframe="1m",
            open_time=1_000_000 + i * 60_000,
            open=price, high=price * 1.001, low=price * 0.999, close=close,
            volume=100.0, close_time=1_000_000 + i * 60_000 + 59_999,
        ))
    return candles


@pytest.fixture
def mock_store():
    store = AsyncMock()
    store.query = AsyncMock(return_value=_make_candles(250))
    store.get_symbols = AsyncMock(return_value=[
        {"market": "binance", "symbol": "BTC/USDT", "timeframe": "1m"}
    ])
    return store


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.set = AsyncMock()
    r.keys = MagicMock(return_value=[])
    return r


@pytest.fixture
def engine(mock_store, mock_redis):
    calc = IndicatorCalculator()
    return IndicatorEngine(store=mock_store, redis_client=mock_redis, calculator=calc)


@pytest.mark.asyncio
async def test_handle_event_writes_to_redis(engine, mock_redis):
    await engine._handle_event("binance", "BTC/USDT", "1m")
    mock_redis.set.assert_called_once()
    key, value = mock_redis.set.call_args[0]
    assert key == "hydra:indicator:binance:BTC/USDT:1m"
    data = json.loads(value)
    assert "RSI_14" in data
    assert "calculated_at" in data


@pytest.mark.asyncio
async def test_handle_event_skips_empty_result(engine, mock_redis, mock_store):
    # Only 5 candles → calculator returns {}
    mock_store.query = AsyncMock(return_value=_make_candles(5))
    await engine._handle_event("binance", "BTC/USDT", "1m")
    mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_does_not_raise_on_exception(engine, mock_store):
    mock_store.query = AsyncMock(side_effect=RuntimeError("db error"))
    # Should not raise — failures must be isolated
    await engine._handle_event("binance", "BTC/USDT", "1m")


@pytest.mark.asyncio
async def test_cold_start_processes_all_symbols(engine, mock_redis, mock_store):
    mock_store.get_symbols = AsyncMock(return_value=[
        {"market": "binance", "symbol": "BTC/USDT", "timeframe": "1m"},
        {"market": "upbit", "symbol": "BTC/KRW", "timeframe": "1h"},
    ])
    await engine.cold_start()
    assert mock_redis.set.call_count == 2
