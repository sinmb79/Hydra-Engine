# hydra/api/supplemental.py
import json
from fastapi import APIRouter, Depends, HTTPException
from hydra.api.auth import verify_api_key

router = APIRouter(prefix="/data")
_redis = None


def set_redis_for_supplemental(redis_client) -> None:
    global _redis
    _redis = redis_client


@router.get("/orderbook")
async def get_orderbook(
    market: str,
    symbol: str,
    _: str = Depends(verify_api_key),
):
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    key = f"hydra:orderbook:{market}:{symbol}"
    raw = _redis.get(key)
    if raw is None:
        raise HTTPException(status_code=404, detail="No orderbook cached for this symbol")
    data = json.loads(raw)
    return {"market": market, "symbol": symbol, **data}


@router.get("/events")
async def get_events(_: str = Depends(verify_api_key)):
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    raw = _redis.get("hydra:events:upcoming")
    if raw is None:
        return []
    return json.loads(raw)


@router.get("/sentiment")
async def get_sentiment(
    symbol: str,
    _: str = Depends(verify_api_key),
):
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    key = f"hydra:sentiment:{symbol}"
    raw = _redis.get(key)
    if raw is None:
        raise HTTPException(status_code=404, detail="No sentiment cached for this symbol")
    data = json.loads(raw)
    return {"symbol": symbol, **data}
