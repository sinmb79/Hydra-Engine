# hydra/api/signals.py
import json
from fastapi import APIRouter, Depends, HTTPException
from hydra.api.auth import verify_api_key

router = APIRouter(prefix="/data")
_redis = None


def set_redis_for_signals(redis_client) -> None:
    global _redis
    _redis = redis_client


@router.get("/signal")
async def get_signal(
    market: str,
    symbol: str,
    timeframe: str,
    _: str = Depends(verify_api_key),
):
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    key = f"hydra:signal:{market}:{symbol}:{timeframe}"
    raw = _redis.get(key)
    if raw is None:
        raise HTTPException(status_code=404, detail="No signal cached for this symbol")
    data = json.loads(raw)
    return {
        "market": market,
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": data["signal"],
        "reason": data["reason"],
        "price": data["price"],
        "ts": data["ts"],
    }


@router.get("/signal/list")
async def list_signals(_: str = Depends(verify_api_key)):
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    keys = _redis.keys("hydra:signal:*")
    result = []
    for key in keys:
        parts = key.split(":")
        if len(parts) >= 5:
            result.append({
                "market": parts[2],
                "symbol": ":".join(parts[3:-1]),
                "timeframe": parts[-1],
            })
    return result
