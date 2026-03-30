import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from hydra.api.auth import verify_api_key

router = APIRouter(prefix="/data")
_redis = None


def set_redis_for_indicators(redis_client) -> None:
    global _redis
    _redis = redis_client


@router.get("/indicators")
async def get_indicators(
    market: str,
    symbol: str,
    timeframe: str,
    _: str = Depends(verify_api_key),
):
    """Return the latest cached indicator values for a symbol."""
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    key = f"hydra:indicator:{market}:{symbol}:{timeframe}"
    raw = _redis.get(key)
    if raw is None:
        raise HTTPException(status_code=404, detail="No indicators cached for this symbol")
    return {
        "market": market,
        "symbol": symbol,
        "timeframe": timeframe,
        "indicators": json.loads(raw),
    }


@router.get("/indicators/list")
async def list_indicators(_: str = Depends(verify_api_key)):
    """Return all (market, symbol, timeframe) tuples that have cached indicators."""
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    keys = _redis.keys("hydra:indicator:*")
    result = []
    for key in keys:
        parts = key.split(":")
        # key format: hydra:indicator:{market}:{symbol}:{timeframe}
        # symbol may contain ":" (e.g. BTC/USDT:USDT for futures)
        # parts[0]="hydra", parts[1]="indicator", parts[2]=market,
        # parts[3:-1]=symbol (joined), parts[-1]=timeframe
        if len(parts) >= 5:
            result.append({
                "market": parts[2],
                "symbol": ":".join(parts[3:-1]),
                "timeframe": parts[-1],
            })
    return result
