from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key

router = APIRouter()


@router.get("/strategies")
async def list_strategies(_: str = Depends(verify_api_key)):
    return {"strategies": [], "note": "Phase 1에서 구현 예정"}


@router.post("/strategies/{name}/start")
async def start_strategy(name: str, _: str = Depends(verify_api_key)):
    return {"status": "not_implemented", "note": "Phase 1에서 구현 예정"}
