# hydra/api/backtest.py
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from hydra.api.auth import verify_api_key
from hydra.backtest.runner import BacktestRunner
from hydra.indicator.calculator import IndicatorCalculator
from hydra.regime.detector import RegimeDetector
from hydra.strategy.signal import SignalGenerator

router = APIRouter(prefix="/backtest")
_store = None


def set_store_for_backtest(store) -> None:
    global _store
    _store = store


class BacktestRequest(BaseModel):
    market: str
    symbol: str
    timeframe: str
    since: int
    until: int
    initial_capital: float = 10000.0
    trade_amount_usd: float = 100.0
    commission_pct: float = 0.001


@router.post("/run")
async def run_backtest(
    req: BacktestRequest,
    _: str = Depends(verify_api_key),
):
    if _store is None:
        raise HTTPException(status_code=503, detail="Store not initialized")
    if req.since >= req.until:
        raise HTTPException(status_code=400, detail="since must be less than until")

    runner = BacktestRunner(
        store=_store,
        calculator=IndicatorCalculator(),
        detector=RegimeDetector(),
        generator=SignalGenerator(),
        initial_capital=req.initial_capital,
        trade_amount_usd=req.trade_amount_usd,
        commission_pct=req.commission_pct,
    )
    try:
        result = await runner.run(
            market=req.market,
            symbol=req.symbol,
            timeframe=req.timeframe,
            since=req.since,
            until=req.until,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return asdict(result)
