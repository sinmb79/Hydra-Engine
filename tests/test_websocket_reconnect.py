import pytest
from unittest.mock import AsyncMock, MagicMock
from hydra.data.models import Candle
from hydra.data.collector import ExchangeCollector


def make_candle() -> Candle:
    return Candle(
        market="binance", symbol="BTC/USDT", timeframe="1m",
        open_time=1_000_000, open=50000.0, high=50100.0,
        low=49900.0, close=50050.0, volume=1.5,
        close_time=1_059_999,
    )


async def _gen_one(candle: Candle):
    yield candle


async def _gen_raise(exc: Exception):
    raise exc
    yield  # makes this an async generator


@pytest.fixture
def mock_store():
    s = AsyncMock()
    s.save = AsyncMock()
    s.get_last_time = AsyncMock(return_value=None)
    return s


@pytest.fixture
def mock_telegram():
    t = AsyncMock()
    t.send_message = AsyncMock()
    return t


async def test_saves_candle_on_receive(mock_store, mock_telegram):
    """Received candle is forwarded to store.save."""
    candle = make_candle()
    handler = MagicMock()
    handler.listen = MagicMock(return_value=_gen_one(candle))

    collector = ExchangeCollector(
        market="binance", handler=handler, store=mock_store,
        backfiller=AsyncMock(), telegram=mock_telegram,
    )
    await collector._run_once()
    mock_store.save.assert_awaited_once_with([candle])


async def test_telegram_alert_after_3_consecutive_failures(mock_store, mock_telegram):
    """Three consecutive disconnects trigger a Telegram alert."""
    handler = MagicMock()
    handler.listen = MagicMock(
        side_effect=lambda: _gen_raise(ConnectionError("down"))
    )
    backfiller = AsyncMock()

    collector = ExchangeCollector(
        market="binance", handler=handler, store=mock_store,
        backfiller=backfiller, telegram=mock_telegram,
        max_delay=0.001,
    )
    await collector._run_with_retry(max_attempts=3)

    mock_telegram.send_message.assert_awaited_once()
    assert "binance" in mock_telegram.send_message.call_args[0][0]


async def test_gap_backfill_called_on_reconnect(mock_store, mock_telegram):
    """After a disconnect, gap_backfill is called on the next connection."""
    candle = make_candle()
    call_count = 0

    async def listen_impl():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("first attempt fails")
        yield candle

    handler = MagicMock()
    handler.listen = MagicMock(side_effect=listen_impl)

    backfiller = AsyncMock()
    backfiller.gap_backfill = AsyncMock()
    fetch_fn_factory = MagicMock(return_value=AsyncMock(return_value=[]))

    collector = ExchangeCollector(
        market="binance", handler=handler, store=mock_store,
        backfiller=backfiller, telegram=mock_telegram,
        symbols=["BTC/USDT"], timeframes=["1m"],
        fetch_fn_factory=fetch_fn_factory,
        max_delay=0.001,
    )
    await collector._run_with_retry(max_attempts=2)

    backfiller.gap_backfill.assert_awaited()
