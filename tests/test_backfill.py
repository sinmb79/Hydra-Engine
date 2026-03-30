import pytest
from unittest.mock import AsyncMock
from hydra.data.models import Candle
from hydra.data.backfill import Backfiller
from hydra.data.storage.base import OhlcvStore


def make_raw_ohlcv(base_time: int, count: int) -> list:
    """Return ccxt fetch_ohlcv-style rows: [ts_ms, o, h, l, c, v]."""
    return [
        [base_time + i * 60_000, 50000.0, 50100.0, 49900.0, 50050.0, 1.5]
        for i in range(count)
    ]


@pytest.fixture
def mock_store():
    store = AsyncMock(spec=OhlcvStore)
    store.get_last_time.return_value = None
    store.save.return_value = None
    return store


async def test_backfill_one_saves_candles(mock_store):
    fetch_fn = AsyncMock(return_value=make_raw_ohlcv(1_000_000, 5))
    filler = Backfiller(mock_store)
    await filler._backfill_one("binance", "BTC/USDT", "1m", fetch_fn=fetch_fn, limit=5)

    mock_store.save.assert_awaited_once()
    saved: list[Candle] = mock_store.save.call_args[0][0]
    assert len(saved) == 5
    assert isinstance(saved[0], Candle)
    assert saved[0].open_time == 1_000_000
    assert saved[0].market == "binance"
    assert saved[0].symbol == "BTC/USDT"
    assert saved[0].timeframe == "1m"
    assert saved[0].close_time == 1_000_000 + 60_000 - 1


async def test_backfill_one_skips_empty_response(mock_store):
    fetch_fn = AsyncMock(return_value=[])
    filler = Backfiller(mock_store)
    await filler._backfill_one("binance", "BTC/USDT", "1m", fetch_fn=fetch_fn)
    mock_store.save.assert_not_awaited()


async def test_gap_backfill_uses_last_time(mock_store):
    mock_store.get_last_time.return_value = 1_060_000
    fetch_fn = AsyncMock(return_value=make_raw_ohlcv(1_060_000, 3))
    filler = Backfiller(mock_store)
    await filler.gap_backfill("binance", "BTC/USDT", "1m", fetch_fn=fetch_fn)

    kwargs = fetch_fn.call_args[1]
    assert kwargs.get("since") == 1_060_000


async def test_gap_backfill_fetches_500_when_no_history(mock_store):
    mock_store.get_last_time.return_value = None
    fetch_fn = AsyncMock(return_value=make_raw_ohlcv(1_000_000, 500))
    filler = Backfiller(mock_store)
    await filler.gap_backfill("binance", "BTC/USDT", "1m", fetch_fn=fetch_fn)

    kwargs = fetch_fn.call_args[1]
    assert kwargs.get("limit") == 500
