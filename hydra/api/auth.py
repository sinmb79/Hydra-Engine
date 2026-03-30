from fastapi import HTTPException, Header
from hydra.config.settings import get_settings

API_KEY_HEADER = "X-HYDRA-KEY"


async def verify_api_key(x_hydra_key: str = Header(..., alias=API_KEY_HEADER)) -> str:
    settings = get_settings()
    if x_hydra_key != settings.hydra_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_hydra_key
