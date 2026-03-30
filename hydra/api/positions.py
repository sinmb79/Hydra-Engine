from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key

router = APIRouter()
_position_tracker = None


def set_position_tracker(tracker) -> None:
    global _position_tracker
    _position_tracker = tracker


@router.get("/positions")
async def get_positions(_: str = Depends(verify_api_key)):
    return {"positions": _position_tracker.get_all()}
