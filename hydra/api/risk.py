from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key

router = APIRouter()
_kill_switch = None
_risk_engine = None


def set_dependencies(kill_switch, risk_engine) -> None:
    global _kill_switch, _risk_engine
    _kill_switch = kill_switch
    _risk_engine = risk_engine


@router.get("/risk")
async def get_risk(_: str = Depends(verify_api_key)):
    return {
        "daily_pnl_pct": _risk_engine.get_daily_pnl_pct(),
        "kill_switch_active": _kill_switch.is_active(),
    }


@router.post("/killswitch")
async def killswitch(reason: str = "manual", _: str = Depends(verify_api_key)):
    result = await _kill_switch.execute(reason=reason, source="api")
    return {"success": result.success, "closed": result.closed_positions, "errors": result.errors}
