# hydra/backtest/result.py
from dataclasses import dataclass, field


@dataclass
class Trade:
    market: str
    symbol: str
    entry_price: float
    exit_price: float
    qty: float
    pnl_usd: float
    pnl_pct: float
    entry_ts: int
    exit_ts: int
    entry_reason: str
    exit_reason: str


@dataclass
class BacktestResult:
    market: str
    symbol: str
    timeframe: str
    since: int
    until: int
    initial_capital: float
    final_equity: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def compute_metrics(
    trades: list[Trade],
    equity_curve: list[dict],
    initial_capital: float,
    final_equity: float,
) -> dict:
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100
    total_trades = len(trades)

    if total_trades == 0:
        return {
            "total_return_pct": round(total_return_pct, 4),
            "total_trades": 0,
            "win_rate": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "avg_pnl_usd": 0.0,
        }

    wins = sum(1 for t in trades if t.pnl_usd > 0)
    win_rate = wins / total_trades * 100
    avg_pnl_usd = sum(t.pnl_usd for t in trades) / total_trades

    # Max drawdown from equity curve
    max_drawdown_pct = 0.0
    if equity_curve:
        peak = equity_curve[0]["equity"]
        for point in equity_curve:
            eq = point["equity"]
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100 if peak > 0 else 0.0
            if dd > max_drawdown_pct:
                max_drawdown_pct = dd

    # Sharpe ratio (annualized, trade-based)
    sharpe_ratio = 0.0
    if total_trades >= 2:
        import math
        pnls = [t.pnl_usd for t in trades]
        mean = sum(pnls) / len(pnls)
        variance = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
        std = math.sqrt(variance)
        if std > 0:
            sharpe_ratio = round((mean / std) * math.sqrt(252), 4)

    return {
        "total_return_pct": round(total_return_pct, 4),
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "sharpe_ratio": sharpe_ratio,
        "avg_pnl_usd": round(avg_pnl_usd, 4),
    }
