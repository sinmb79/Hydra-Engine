# hydra/backtest/runner.py
from hydra.backtest.broker import BacktestBroker
from hydra.backtest.result import BacktestResult, compute_metrics
from hydra.data.storage.base import OhlcvStore
from hydra.indicator.calculator import IndicatorCalculator
from hydra.regime.detector import RegimeDetector
from hydra.strategy.signal import SignalGenerator

_WARMUP = 210  # IndicatorCalculator._MIN_CANDLES


class BacktestRunner:
    def __init__(
        self,
        store: OhlcvStore,
        calculator: IndicatorCalculator,
        detector: RegimeDetector,
        generator: SignalGenerator,
        initial_capital: float = 10000.0,
        trade_amount_usd: float = 100.0,
        commission_pct: float = 0.001,
    ):
        self._store = store
        self._calculator = calculator
        self._detector = detector
        self._generator = generator
        self._initial_capital = initial_capital
        self._trade_amount = trade_amount_usd
        self._commission = commission_pct

    async def run(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
    ) -> BacktestResult:
        if since >= until:
            raise ValueError(f"since ({since}) must be less than until ({until})")

        candles = await self._store.query(
            market=market,
            symbol=symbol,
            timeframe=timeframe,
            limit=100_000,
            since=None,
        )
        # Filter to candles up to 'until'
        candles = [c for c in candles if c.open_time <= until]

        broker = BacktestBroker(
            initial_capital=self._initial_capital,
            trade_amount_usd=self._trade_amount,
            commission_pct=self._commission,
        )

        # Find the first index where trading starts: open_time >= since AND index >= WARMUP
        trading_start_idx = None
        for i, c in enumerate(candles):
            if c.open_time >= since and i >= _WARMUP:
                trading_start_idx = i
                break

        if trading_start_idx is None:
            return BacktestResult(
                market=market,
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                until=until,
                initial_capital=self._initial_capital,
                final_equity=self._initial_capital,
                trades=[],
                equity_curve=[],
                metrics=compute_metrics([], [], self._initial_capital, self._initial_capital),
            )

        for i in range(trading_start_idx, len(candles)):
            window = candles[i - _WARMUP + 1: i + 1]
            indicators = self._calculator.compute(window)
            if not indicators:
                continue
            candle = candles[i]
            close = candle.close
            indicators["close"] = close
            regime = self._detector.detect(indicators, close)
            signal = self._generator.generate(indicators, regime, close)
            broker.on_signal(signal, candle)

        # Close any open position at end of backtest
        if candles:
            last = candles[-1]
            broker.close_open_position(
                price=last.close, ts=last.open_time, reason="backtest_end"
            )

        trades = broker.trades
        for t in trades:
            t.market = market
            t.symbol = symbol

        equity_curve = broker.equity_curve
        final_equity = broker.equity
        metrics = compute_metrics(trades, equity_curve, self._initial_capital, final_equity)

        return BacktestResult(
            market=market,
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            until=until,
            initial_capital=self._initial_capital,
            final_equity=round(final_equity, 6),
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
        )
