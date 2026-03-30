import pytest
from hydra.data.models import Candle
from hydra.data.storage.sqlite import SqliteStore


def test_store_exposes_close():
    assert hasattr(SqliteStore, "close")


def make_candle(open_time: int, market="binance", symbol="BTC/USDT", tf="1m") -> Candle:
    return Candle(
        market=market, symbol=symbol, timeframe=tf,
        open_time=open_time, open=50000.0, high=50100.0,
        low=49900.0, close=50050.0, volume=1.5,
        close_time=open_time + 59999,
    )


@pytest.fixture
async def store(tmp_path):
    s = SqliteStore(db_path=str(tmp_path / "test.db"))
    await s.init()
    try:
        yield s
    finally:
        await s.close()


async def test_save_and_query(store):
    candles = [make_candle(1_000_000 + i * 60_000) for i in range(5)]
    await store.save(candles)
    result = await store.query("binance", "BTC/USDT", "1m", limit=10)
    assert len(result) == 5
    assert result[0].open_time == 1_000_000
    assert result[-1].open_time == 1_000_000 + 4 * 60_000


async def test_upsert_updates_close(store):
    await store.save([make_candle(1_000_000)])
    updated = Candle(
        market="binance", symbol="BTC/USDT", timeframe="1m",
        open_time=1_000_000, open=50000.0, high=50200.0,
        low=49800.0, close=50150.0, volume=2.0,
        close_time=1_059_999,
    )
    await store.save([updated])
    result = await store.query("binance", "BTC/USDT", "1m")
    assert len(result) == 1
    assert result[0].close == 50150.0


async def test_get_last_time_empty(store):
    assert await store.get_last_time("binance", "BTC/USDT", "1m") is None


async def test_get_last_time(store):
    candles = [make_candle(1_000_000 + i * 60_000) for i in range(3)]
    await store.save(candles)
    result = await store.get_last_time("binance", "BTC/USDT", "1m")
    assert result == 1_000_000 + 2 * 60_000


async def test_query_with_since(store):
    candles = [make_candle(1_000_000 + i * 60_000) for i in range(5)]
    await store.save(candles)
    result = await store.query("binance", "BTC/USDT", "1m", since=1_000_000 + 2 * 60_000)
    assert len(result) == 3
    assert result[0].open_time == 1_000_000 + 2 * 60_000


async def test_get_symbols(store):
    await store.save([make_candle(1_000_000, market="binance", symbol="BTC/USDT")])
    await store.save([make_candle(1_000_000, market="upbit", symbol="BTC/KRW")])
    symbols = await store.get_symbols()
    assert len(symbols) == 2
    markets = {s["market"] for s in symbols}
    assert "binance" in markets
    assert "upbit" in markets


async def test_close_is_idempotent(tmp_path):
    store = SqliteStore(db_path=str(tmp_path / "test-close.db"))
    await store.init()
    await store.close()
    await store.close()
