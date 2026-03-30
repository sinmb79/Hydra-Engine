from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key

router = APIRouter()
_market_manager = None


def set_market_manager(mm) -> None:
    global _market_manager
    _market_manager = mm


@router.get("/markets")
async def get_markets(_: str = Depends(verify_api_key)):
    return {"active": _market_manager.get_active_markets()}


@router.post("/markets/{market_id}/enable")
async def enable_market(market_id: str, _: str = Depends(verify_api_key)):
    _market_manager.enable(market_id)
    return {"status": "enabled", "market": market_id}


@router.post("/markets/{market_id}/disable")
async def disable_market(market_id: str, _: str = Depends(verify_api_key)):
    _market_manager.disable(market_id)
    return {"status": "disabled", "market": market_id}
