import hydra
from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key
from hydra.config.settings import get_settings

router = APIRouter()


@router.get("/status")
async def status(_: str = Depends(verify_api_key)):
    settings = get_settings()
    return {
        "version": hydra.__version__,
        "profile": settings.hydra_profile,
    }


@router.get("/modules")
async def modules(_: str = Depends(verify_api_key)):
    return {"modules": ["core", "resilience", "exchange", "notify"]}
