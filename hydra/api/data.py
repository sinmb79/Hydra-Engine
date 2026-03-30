from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from hydra.api.auth import verify_api_key
from hydra.data.storage.base import OhlcvStore

router = APIRouter(prefix="/data")
_store: Optional[OhlcvStore] = None


def set_store(store: OhlcvStore) -> None:
    global _store
    _store = store


@router.get("/candles")
async def get_candles(
    market: str,
    symbol: str,
    timeframe: str,
    limit: int = Query(default=200, ge=1, le=1000),
    since: Optional[int] = None,
    _: str = Depends(verify_api_key),
):
    """Return OHLCV candles ordered by open_time ASC."""
    if _store is None:
        raise HTTPException(status_code=503, detail="Store not initialized")
    candles = await _store.query(market, symbol, timeframe, limit=limit, since=since)
    return [
        {
            "market": c.market,
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "open_time": c.open_time,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
            "close_time": c.close_time,
        }
        for c in candles
    ]


@router.get("/symbols")
async def get_symbols(_: str = Depends(verify_api_key)):
    """Return distinct {market, symbol, timeframe} records being collected."""
    if _store is None:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return await _store.get_symbols()
