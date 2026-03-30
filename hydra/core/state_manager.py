import json
import time
from typing import Any

from hydra.logging.setup import get_logger

logger = get_logger(__name__)

STATE_KEY = "hydra:state"


class StateManager:
    def __init__(self, redis_client):
        self._redis = redis_client

    def save(self, key: str, value: Any) -> None:
        payload = json.dumps({"value": value, "ts": time.time()})
        self._redis.hset(STATE_KEY, key, payload)

    def load(self, key: str, default: Any = None) -> Any:
        raw = self._redis.hget(STATE_KEY, key)
        if raw is None:
            return default
        return json.loads(raw)["value"]

    def save_all(self, state: dict) -> None:
        for k, v in state.items():
            self.save(k, v)

    def load_all(self) -> dict:
        raw = self._redis.hgetall(STATE_KEY)
        return {k: json.loads(v)["value"] for k, v in raw.items()}
