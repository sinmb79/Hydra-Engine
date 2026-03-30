from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key

router = APIRouter()
_pnl_tracker = None
_position_tracker = None


def set_pnl_dependencies(pnl_tracker, position_tracker) -> None:
    global _pnl_tracker, _position_tracker
    _pnl_tracker = pnl_tracker
    _position_tracker = position_tracker


@router.get("/pnl")
async def get_pnl(_: str = Depends(verify_api_key)):
    """전체 시스템 손익 현황."""
    positions = _position_tracker.get_all()
    return _pnl_tracker.get_summary(positions)


@router.post("/pnl/reset-daily")
async def reset_daily_pnl(_: str = Depends(verify_api_key)):
    """일일 손익 초기화."""
    _pnl_tracker.reset_daily()
    return {"status": "reset"}
