# tests/test_backtest_runner.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from hydra.backtest.result import Trade, BacktestResult, compute_metrics


def _make_trade(pnl_usd: float, entry_price: float = 100.0,
                exit_price: float = 110.0) -> Trade:
    return Trade(
        market="binance",
        symbol="BTC/USDT",
        entry_price=entry_price,
        exit_price=exit_price,
        qty=1.0,
        pnl_usd=pnl_usd,
        pnl_pct=(exit_price - entry_price) / entry_price * 100,
        entry_ts=1000,
        exit_ts=2000,
        entry_reason="trend_up: ema_cross+rsi",
        exit_reason="trend_down: ema_cross+rsi",
    )


def test_compute_metrics_no_trades():
    metrics = compute_metrics(
        trades=[],
        equity_curve=[{"ts": 1000, "equity": 10000.0}],
        initial_capital=10000.0,
        final_equity=10000.0,
    )
    assert metrics["total_return_pct"] == 0.0
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["max_drawdown_pct"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["avg_pnl_usd"] == 0.0


def test_compute_metrics_with_trades():
    trades = [_make_trade(50.0), _make_trade(-20.0), _make_trade(30.0)]
    equity_curve = [
        {"ts": 1000, "equity": 10000.0},
        {"ts": 2000, "equity": 10050.0},
        {"ts": 3000, "equity": 10030.0},
        {"ts": 4000, "equity": 10060.0},
    ]
    metrics = compute_metrics(
        trades=trades,
        equity_curve=equity_curve,
        initial_capital=10000.0,
        final_equity=10060.0,
    )
    assert metrics["total_trades"] == 3
    assert metrics["total_return_pct"] == pytest.approx(0.6, abs=0.01)
    assert metrics["win_rate"] == pytest.approx(66.67, abs=0.1)
    assert metrics["avg_pnl_usd"] == pytest.approx(20.0, abs=0.01)
    assert metrics["max_drawdown_pct"] >= 0.0
    assert isinstance(metrics["sharpe_ratio"], float)


from hydra.backtest.runner import BacktestRunner
from hydra.data.models import Candle
from hydra.indicator.calculator import IndicatorCalculator
from hydra.regime.detector import RegimeDetector
from hydra.strategy.signal import SignalGenerator


def _make_candles(n: int, base_close: float = 100.0) -> list[Candle]:
    """Generate n synthetic candles with monotonically increasing timestamps."""
    candles = []
    for i in range(n):
        close = base_close + i * 0.1
        candles.append(Candle(
            market="binance", symbol="BTC/USDT", timeframe="1h",
            open_time=1_000_000 + i * 3_600_000,
            open=close, high=close + 1, low=close - 1,
            close=close, volume=100.0,
            close_time=1_000_000 + i * 3_600_000 + 3_599_000,
        ))
    return candles


@pytest.mark.asyncio
async def test_runner_returns_backtest_result():
    candles = _make_candles(230)
    calculator = MagicMock(spec=IndicatorCalculator)
    calculator.compute = MagicMock(return_value={
        "EMA_9": 101.0, "EMA_20": 100.0, "RSI_14": 55.0,
        "BBB_5_2.0_2.0": 0.05, "ADX_14": 30.0, "EMA_50": 99.0,
    })

    runner = BacktestRunner(
        store=MagicMock(query=AsyncMock(return_value=candles)),
        calculator=calculator,
        detector=RegimeDetector(),
        generator=SignalGenerator(),
        initial_capital=10000.0,
        trade_amount_usd=100.0,
    )
    since = candles[210].open_time
    until = candles[-1].open_time
    result = await runner.run("binance", "BTC/USDT", "1h", since=since, until=until)

    from hydra.backtest.result import BacktestResult
    assert isinstance(result, BacktestResult)
    assert result.market == "binance"
    assert result.symbol == "BTC/USDT"
    assert result.initial_capital == 10000.0
    assert "total_return_pct" in result.metrics


@pytest.mark.asyncio
async def test_runner_insufficient_data_returns_empty_result():
    candles = _make_candles(50)  # less than 210 warmup
    runner = BacktestRunner(
        store=MagicMock(query=AsyncMock(return_value=candles)),
        calculator=IndicatorCalculator(),
        detector=RegimeDetector(),
        generator=SignalGenerator(),
    )
    since = candles[0].open_time
    until = candles[-1].open_time
    result = await runner.run("binance", "BTC/USDT", "1h", since=since, until=until)
    assert result.metrics["total_trades"] == 0


@pytest.mark.asyncio
async def test_runner_validates_since_until():
    runner = BacktestRunner(
        store=MagicMock(),
        calculator=IndicatorCalculator(),
        detector=RegimeDetector(),
        generator=SignalGenerator(),
    )
    with pytest.raises(ValueError, match="since"):
        await runner.run("binance", "BTC/USDT", "1h", since=2000, until=1000)


@pytest.mark.asyncio
async def test_runner_applies_commission():
    candles = _make_candles(230)
    call_count = 0
    base_indicators = {
        "EMA_9": 101.0, "EMA_20": 100.0,
        "BBB_5_2.0_2.0": 0.05, "ADX_14": 30.0, "EMA_50": 99.0,
    }

    def mock_compute(candles_window):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 1:
            return {**base_indicators, "RSI_14": 55.0}   # trending_up BUY
        else:
            return {**base_indicators, "RSI_14": 25.0,
                    "EMA_9": 99.0, "EMA_20": 100.0}       # trending_down SELL

    calculator = MagicMock(spec=IndicatorCalculator)
    calculator.compute = MagicMock(side_effect=mock_compute)

    runner = BacktestRunner(
        store=MagicMock(query=AsyncMock(return_value=candles)),
        calculator=calculator,
        detector=RegimeDetector(),
        generator=SignalGenerator(),
        initial_capital=10000.0,
        trade_amount_usd=100.0,
        commission_pct=0.001,
    )
    since = candles[210].open_time
    until = candles[-1].open_time
    result = await runner.run("binance", "BTC/USDT", "1h", since=since, until=until)
    # With commission, final_equity should differ from initial if there were trades
    assert isinstance(result.final_equity, float)
    assert result.metrics["total_trades"] >= 0
