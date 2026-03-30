# tests/test_backtest_broker.py
import pytest
from hydra.backtest.broker import BacktestBroker
from hydra.backtest.result import Trade
from hydra.data.models import Candle
from hydra.strategy.signal import Signal


def _make_candle(close: float, ts: int = 1000) -> Candle:
    return Candle(
        market="binance", symbol="BTC/USDT", timeframe="1h",
        open_time=ts, open=close, high=close, low=close,
        close=close, volume=1.0, close_time=ts + 3600000,
    )


def _make_signal(sig: str, price: float, reason: str = "test") -> Signal:
    return Signal(signal=sig, reason=reason, price=price, ts=1000)


def test_buy_opens_position():
    broker = BacktestBroker(initial_capital=10000.0, trade_amount_usd=100.0,
                            commission_pct=0.0)
    broker.on_signal(_make_signal("BUY", 100.0), _make_candle(100.0, ts=1000))
    assert len(broker.trades) == 0  # trade recorded only on close
    assert broker.equity == pytest.approx(10000.0, abs=0.01)


def test_sell_closes_position_and_records_trade():
    broker = BacktestBroker(initial_capital=10000.0, trade_amount_usd=100.0,
                            commission_pct=0.0)
    broker.on_signal(_make_signal("BUY", 100.0), _make_candle(100.0, ts=1000))
    broker.on_signal(_make_signal("SELL", 110.0), _make_candle(110.0, ts=2000))
    assert len(broker.trades) == 1
    trade = broker.trades[0]
    assert trade.entry_price == 100.0
    assert trade.exit_price == 110.0
    assert trade.pnl_usd == pytest.approx(10.0, abs=0.01)   # 1.0 qty * 10 price diff
    assert broker.equity == pytest.approx(10010.0, abs=0.01)


def test_sell_without_position_is_ignored():
    broker = BacktestBroker(initial_capital=10000.0, trade_amount_usd=100.0)
    broker.on_signal(_make_signal("SELL", 110.0), _make_candle(110.0))
    assert len(broker.trades) == 0
    assert broker.equity == pytest.approx(10000.0, abs=0.01)


def test_force_close_records_trade():
    broker = BacktestBroker(initial_capital=10000.0, trade_amount_usd=100.0,
                            commission_pct=0.0)
    broker.on_signal(_make_signal("BUY", 100.0), _make_candle(100.0, ts=1000))
    broker.close_open_position(price=120.0, ts=9000, reason="backtest_end")
    assert len(broker.trades) == 1
    assert broker.trades[0].exit_price == 120.0
    assert broker.trades[0].pnl_usd == pytest.approx(20.0, abs=0.01)
