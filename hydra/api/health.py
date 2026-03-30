import time
from fastapi import APIRouter

router = APIRouter()
_START_TIME = time.time()
_redis = None


def set_redis(redis_client) -> None:
    global _redis
    _redis = redis_client


@router.get("/health")
async def health():
    result = {
        "status": "ok",
        "uptime_seconds": int(time.time() - _START_TIME),
    }
    if _redis:
        keys = _redis.keys("hydra:collector:*:status")
        collectors = {}
        for key in keys:
            market = key.split(":")[2]
            collectors[market] = _redis.get(key)
        if collectors:
            result["collectors"] = collectors
            if any(v and v.startswith("error:") for v in collectors.values()):
                result["status"] = "degraded"
    return result
