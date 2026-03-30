# hydra/backtest/broker.py
from hydra.backtest.result import Trade
from hydra.data.models import Candle
from hydra.strategy.signal import Signal


class BacktestBroker:
    def __init__(
        self,
        initial_capital: float,
        trade_amount_usd: float,
        commission_pct: float = 0.001,
    ):
        self._capital = initial_capital
        self._trade_amount = trade_amount_usd
        self._commission = commission_pct
        self._position: dict | None = None   # {entry_price, qty, entry_ts, entry_reason}
        self._trades: list[Trade] = []
        self._equity_curve: list[dict] = []

    def on_signal(self, signal: Signal, candle: Candle) -> None:
        if signal.signal == "BUY" and self._position is None:
            qty = self._trade_amount / candle.close
            commission = self._trade_amount * self._commission
            self._capital -= commission
            self._position = {
                "entry_price": candle.close,
                "qty": qty,
                "entry_ts": candle.open_time,
                "entry_reason": signal.reason,
            }
        elif signal.signal == "SELL" and self._position is not None:
            self.close_open_position(
                price=candle.close,
                ts=candle.open_time,
                reason=signal.reason,
            )
        self._equity_curve.append({"ts": candle.open_time, "equity": self.equity})

    def close_open_position(
        self, price: float, ts: int, reason: str = "backtest_end"
    ) -> None:
        if self._position is None:
            return
        pos = self._position
        gross_pnl = (price - pos["entry_price"]) * pos["qty"]
        commission = price * pos["qty"] * self._commission
        net_pnl = gross_pnl - commission
        pnl_pct = (price - pos["entry_price"]) / pos["entry_price"] * 100
        self._capital += net_pnl
        self._trades.append(Trade(
            market="",
            symbol="",
            entry_price=pos["entry_price"],
            exit_price=price,
            qty=pos["qty"],
            pnl_usd=round(net_pnl, 6),
            pnl_pct=round(pnl_pct, 4),
            entry_ts=pos["entry_ts"],
            exit_ts=ts,
            entry_reason=pos["entry_reason"],
            exit_reason=reason,
        ))
        self._position = None
        self._equity_curve.append({"ts": ts, "equity": self.equity})

    @property
    def trades(self) -> list[Trade]:
        return self._trades

    @property
    def equity_curve(self) -> list[dict]:
        return self._equity_curve

    @property
    def equity(self) -> float:
        return self._capital
